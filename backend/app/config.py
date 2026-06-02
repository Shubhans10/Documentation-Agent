"""DocuForge configuration — loads settings from environment variables."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the backend directory
_backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(_backend_dir / ".env")


class Settings:
    """Application settings loaded from environment."""

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    OUTPUT_DIR: Path = Path(os.getenv("OUTPUT_DIR", str(_backend_dir / "output")))
    UPLOAD_DIR: Path = _backend_dir / "uploads"
    TEMPLATES_DIR: Path = Path(__file__).resolve().parent / "templates"

    # Allowed file extensions for upload
    ALLOWED_EXTENSIONS: set[str] = {
        ".txt", ".pdf", ".md", ".markdown",
        ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg",
    }

    # Image extensions (subset of allowed)
    IMAGE_EXTENSIONS: set[str] = {
        ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg",
    }

    MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024

    def __init__(self) -> None:
        # Create directories if they don't exist
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    def validate(self) -> None:
        """Validate required settings on startup."""
        if not self.GEMINI_API_KEY or self.GEMINI_API_KEY == "your_api_key_here":
            raise ValueError(
                "GEMINI_API_KEY is not set. "
                "Get one at https://aistudio.google.com/app/api-keys "
                "and add it to your .env file."
            )


settings = Settings()
