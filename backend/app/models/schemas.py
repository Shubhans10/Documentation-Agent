"""Pydantic models for API request/response schemas."""

from __future__ import annotations

import uuid
from enum import Enum
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class FileType(str, Enum):
    TEXT = "text"
    PDF = "pdf"
    MARKDOWN = "markdown"
    IMAGE = "image"


class Theme(str, Enum):
    MODERN_DARK = "modern_dark"
    CLEAN_LIGHT = "clean_light"
    TECHNICAL_BLUEPRINT = "technical_blueprint"


class ImagePlacement(str, Enum):
    HERO_BANNER = "hero_banner"
    AFTER_SECTION = "after_section"
    APPENDIX = "appendix"
    INLINE = "inline"
    SKIP = "skip"


class GenerationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    AWAITING_INPUT = "awaiting_input"
    COMPLETE = "complete"
    ERROR = "error"


# ---------------------------------------------------------------------------
# File & Upload
# ---------------------------------------------------------------------------

class UploadedFileInfo(BaseModel):
    """Metadata about a single uploaded file."""
    file_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    file_type: FileType
    size_bytes: int
    is_image: bool = False
    preview_url: str | None = None  # For images — base64 data URI


class UploadResponse(BaseModel):
    """Response after uploading files."""
    files: list[UploadedFileInfo]
    images_detected: list[UploadedFileInfo] = []
    message: str = "Files uploaded successfully"


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

class GenerateRequest(BaseModel):
    """Request to start documentation generation."""
    file_ids: list[str]
    title: str = "Documentation"
    theme: Theme = Theme.MODERN_DARK
    enable_diagrams: bool = True
    enable_toc: bool = True
    enable_code_highlighting: bool = True
    embed_images: bool = True
    additional_instructions: str = ""


class GenerateProgress(BaseModel):
    """SSE event for generation progress."""
    task_id: str
    status: GenerationStatus
    progress: float = 0.0  # 0.0 to 1.0
    current_step: str = ""
    message: str = ""
    html_preview: str | None = None
    image_placement_required: ImagePlacementInfo | None = None


class ImagePlacementInfo(BaseModel):
    """Info sent to frontend when an image needs placement."""
    image_id: str
    filename: str
    preview_url: str
    available_sections: list[str] = []


class ImagePlacementRequest(BaseModel):
    """User's decision on where to place an image."""
    task_id: str
    image_id: str
    placement: ImagePlacement
    section_id: str | None = None  # Required when placement is AFTER_SECTION


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    """A message in the chat interface."""
    task_id: str
    message: str


class ChatResponse(BaseModel):
    """Response from the agent via chat."""
    message: str
    updated_preview: bool = False


# ---------------------------------------------------------------------------
# Document Structure (agent output)
# ---------------------------------------------------------------------------

class DocumentSection(BaseModel):
    """A section in the generated documentation."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    level: int = 2  # h2 by default
    content_html: str = ""
    diagrams: list[str] = []  # Mermaid code blocks
    tables: list[str] = []    # HTML table strings
    code_blocks: list[str] = []  # HTML code blocks
    images: list[dict] = []   # {src, alt, caption}


class GeneratedDocument(BaseModel):
    """Full generated document structure."""
    task_id: str
    title: str
    theme: Theme
    sections: list[DocumentSection] = []
    toc_html: str = ""
    full_html: str = ""
    word_count: int = 0
    diagram_count: int = 0
    section_count: int = 0
