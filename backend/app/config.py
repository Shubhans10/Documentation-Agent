"""DocuForge configuration — loads settings from environment variables.

Supports two mutually-exclusive authentication modes for the LLM:
  * ``api_key``   — Gemini Developer API (``GEMINI_API_KEY``)
  * ``vertex_sa`` — Vertex AI with a GCP service-account JSON
                    (``GOOGLE_APPLICATION_CREDENTIALS``)

API key wins when both are present.
"""

import json
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

# Load .env from the backend directory
_backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(_backend_dir / ".env")


# ─── Corporate TLS interception (Zscaler / proxies) ──────────────────────────
# If CUSTOM_CA_BUNDLE points to a PEM, merge it with certifi's bundle and
# export the standard SSL env vars so every HTTPS client (google-genai,
# google-auth, httpx, requests, urllib) trusts it. Runs at import time so it
# is in effect before any client is built.
def _install_custom_ca() -> str | None:
    custom = os.getenv("CUSTOM_CA_BUNDLE", "").strip()
    if not custom:
        return None
    custom_path = Path(custom)
    if not custom_path.is_file():
        return None

    custom_pem = custom_path.read_bytes()

    # 1. Inject into certifi's cacert.pem so every library that calls
    #    certifi.where() (requests, httpx, urllib3, google-auth, google-genai)
    #    trusts the corporate root automatically.
    try:
        import certifi
        certifi_pem_path = Path(certifi.where())
        existing = certifi_pem_path.read_bytes()
        marker = b"# --- DocuForge Custom CA ---"
        if marker not in existing:
            certifi_pem_path.write_bytes(
                existing + b"\n" + marker + b"\n" + custom_pem
            )
    except Exception:
        pass

    # 2. Also write a combined bundle and export env vars for clients that
    #    don't use certifi (raw ssl, grpc, curl).
    try:
        certifi_bundle = Path(certifi.where()).read_bytes()
    except Exception:
        certifi_bundle = b""
    combined = _backend_dir / ".ca-bundle-combined.pem"
    header = f"\n# --- custom CA ({custom_path}) ---\n".encode("utf-8")
    combined.write_bytes(certifi_bundle + header + custom_pem)
    bundle_str = str(combined)
    for var in ("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE",
                "GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"):
        os.environ[var] = bundle_str  # force-set, not setdefault
    return bundle_str


_ACTIVE_CA_BUNDLE = _install_custom_ca()


# ─── Relax OpenSSL strict X.509 check ────────────────────────────────────────
# Some corporate roots (Zscaler) are issued with `Basic Constraints` not
# marked critical. OpenSSL's strict mode — enabled by urllib3 — rejects them
# with "Basic Constraints of CA cert not marked critical". We clear that
# single flag globally while keeping full certificate-chain verification.
def _relax_strict_x509() -> None:
    import ssl
    strict = getattr(ssl, "VERIFY_X509_STRICT", 0)
    if not strict:
        return

    _orig_create = ssl.create_default_context

    def _patched(*args, **kwargs):
        ctx = _orig_create(*args, **kwargs)
        ctx.verify_flags &= ~strict
        return ctx

    ssl.create_default_context = _patched  # type: ignore[assignment]
    # urllib3 caches its own context — clear the strict flag there too.
    # urllib3.connection imports `create_urllib3_context` by name, so we
    # must patch BOTH the source module and the already-bound reference.
    try:
        import urllib3.util.ssl_ as _u3ssl
        _orig_u3 = _u3ssl.create_urllib3_context

        def _patched_u3(*args, **kwargs):
            ctx = _orig_u3(*args, **kwargs)
            ctx.verify_flags &= ~strict
            return ctx

        _u3ssl.create_urllib3_context = _patched_u3  # type: ignore[assignment]
        try:
            import urllib3.connection as _u3conn
            _u3conn.create_urllib3_context = _patched_u3  # type: ignore[assignment]
        except Exception:
            pass
    except Exception:
        pass


if _ACTIVE_CA_BUNDLE:
    _relax_strict_x509()


AuthMode = Literal["api_key", "vertex_sa"]


class Settings:
    """Application settings loaded from environment."""

    # ── LLM auth ────────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS", ""
    ).strip()
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "").strip()
    GCP_LOCATION: str = os.getenv("GCP_LOCATION", "us-central1").strip() or "us-central1"
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-pro").strip() or "gemini-2.5-pro"

    # ── Files ───────────────────────────────────────────────────────────────
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    OUTPUT_DIR: Path = Path(os.getenv("OUTPUT_DIR", str(_backend_dir / "output")))
    UPLOAD_DIR: Path = _backend_dir / "uploads"
    TEMPLATES_DIR: Path = Path(__file__).resolve().parent / "templates"

    ALLOWED_EXTENSIONS: set[str] = {
        ".txt", ".pdf", ".md", ".markdown",
        ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg",
    }
    IMAGE_EXTENSIONS: set[str] = {
        ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg",
    }

    MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024

    def __init__(self) -> None:
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # ── Auth helpers ────────────────────────────────────────────────────────
    @property
    def auth_mode(self) -> AuthMode | None:
        if self.GEMINI_API_KEY and self.GEMINI_API_KEY != "your_api_key_here":
            return "api_key"
        if self.GOOGLE_APPLICATION_CREDENTIALS:
            return "vertex_sa"
        return None

    def resolved_project_id(self) -> str:
        """Best-effort project id for Vertex AI: explicit env > SA JSON."""
        if self.GCP_PROJECT_ID:
            return self.GCP_PROJECT_ID
        sa_path = Path(self.GOOGLE_APPLICATION_CREDENTIALS)
        if sa_path.is_file():
            try:
                return json.loads(sa_path.read_text(encoding="utf-8")).get("project_id", "")
            except (OSError, ValueError):
                return ""
        return ""

    def validate(self) -> None:
        """Validate auth configuration on startup."""
        mode = self.auth_mode
        if mode is None:
            raise ValueError(
                "No LLM credentials configured. Set either GEMINI_API_KEY "
                "(https://aistudio.google.com/app/api-keys) "
                "or GOOGLE_APPLICATION_CREDENTIALS (path to a GCP service-account JSON) "
                "in your .env file."
            )
        if mode == "vertex_sa":
            sa_path = Path(self.GOOGLE_APPLICATION_CREDENTIALS)
            if not sa_path.is_file():
                raise ValueError(
                    f"GOOGLE_APPLICATION_CREDENTIALS points to a non-existent file: {sa_path}"
                )
            if not self.resolved_project_id():
                raise ValueError(
                    "Cannot determine GCP project id. Set GCP_PROJECT_ID or ensure "
                    "the service-account JSON contains a 'project_id' field."
                )


settings = Settings()

