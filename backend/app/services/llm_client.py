"""LLM client factory — builds a `google.genai.Client` for either auth mode.

The unified `google-genai` SDK supports both targets:
  * **Gemini Developer API** — when constructed with ``api_key=``
  * **Vertex AI**            — when constructed with ``vertexai=True``,
                               ``project=``, ``location=``, and (optionally)
                               explicit ``credentials=`` from a service-account
                               JSON file.

Callers should not import the SDK directly; use :func:`build_client`.
"""

from __future__ import annotations

from functools import lru_cache

from google import genai

from app.config import settings


@lru_cache(maxsize=1)
def build_client() -> genai.Client:
    """Return a cached `genai.Client` configured per the active auth mode."""
    mode = settings.auth_mode
    if mode == "api_key":
        return genai.Client(api_key=settings.GEMINI_API_KEY)

    if mode == "vertex_sa":
        # Import lazily so the dependency is only required on this path.
        from google.oauth2 import service_account

        credentials = service_account.Credentials.from_service_account_file(
            settings.GOOGLE_APPLICATION_CREDENTIALS,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        return genai.Client(
            vertexai=True,
            project=settings.resolved_project_id(),
            location=settings.GCP_LOCATION,
            credentials=credentials,
        )

    raise RuntimeError(
        "No LLM credentials configured — call settings.validate() at startup."
    )


def describe_auth() -> dict[str, str]:
    """Return a small dict describing the active auth mode (for /health)."""
    mode = settings.auth_mode
    if mode == "api_key":
        return {"mode": "api_key", "model": settings.GEMINI_MODEL}
    if mode == "vertex_sa":
        return {
            "mode": "vertex_sa",
            "model": settings.GEMINI_MODEL,
            "project": settings.resolved_project_id(),
            "location": settings.GCP_LOCATION,
        }
    return {"mode": "unconfigured", "model": settings.GEMINI_MODEL}
