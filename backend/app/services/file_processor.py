"""File processing pipeline — extracts content from TXT, PDF, Markdown and detects images."""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path

import markdown as md_lib
from PIL import Image as PILImage
from PyPDF2 import PdfReader

from app.config import settings
from app.models.schemas import FileType, UploadedFileInfo


class ProcessedFile:
    """Result of processing a single uploaded file."""

    def __init__(
        self,
        file_info: UploadedFileInfo,
        text_content: str = "",
        html_content: str = "",
        image_data: str | None = None,      # base64 data-uri for images
        image_dimensions: tuple[int, int] | None = None,
        page_count: int = 0,
    ) -> None:
        self.file_info = file_info
        self.text_content = text_content
        self.html_content = html_content
        self.image_data = image_data
        self.image_dimensions = image_dimensions
        self.page_count = page_count


def detect_file_type(filename: str) -> FileType:
    """Determine the FileType from the file extension."""
    ext = Path(filename).suffix.lower()
    if ext in settings.IMAGE_EXTENSIONS:
        return FileType.IMAGE
    if ext == ".pdf":
        return FileType.PDF
    if ext in {".md", ".markdown"}:
        return FileType.MARKDOWN
    return FileType.TEXT


def process_text_file(file_path: Path, file_info: UploadedFileInfo) -> ProcessedFile:
    """Read a plain text file and return its content."""
    text = file_path.read_text(encoding="utf-8", errors="replace")
    return ProcessedFile(
        file_info=file_info,
        text_content=text,
        html_content=f"<pre>{text}</pre>",
    )


def process_pdf_file(file_path: Path, file_info: UploadedFileInfo) -> ProcessedFile:
    """Extract text from a PDF file page by page."""
    reader = PdfReader(str(file_path))
    pages: list[str] = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        pages.append(page_text)

    full_text = "\n\n--- Page Break ---\n\n".join(pages)
    return ProcessedFile(
        file_info=file_info,
        text_content=full_text,
        html_content=f"<pre>{full_text}</pre>",
        page_count=len(reader.pages),
    )


def process_markdown_file(file_path: Path, file_info: UploadedFileInfo) -> ProcessedFile:
    """Convert Markdown to HTML while preserving the raw text."""
    raw = file_path.read_text(encoding="utf-8", errors="replace")
    html = md_lib.markdown(
        raw,
        extensions=["extra", "codehilite", "toc", "tables", "fenced_code"],
    )
    return ProcessedFile(
        file_info=file_info,
        text_content=raw,
        html_content=html,
    )


def process_image_file(file_path: Path, file_info: UploadedFileInfo) -> ProcessedFile:
    """Read an image file, extract metadata, and create a base64 data URI."""
    mime_type = mimetypes.guess_type(str(file_path))[0] or "image/png"

    # Handle SVGs separately (they are text-based)
    if file_path.suffix.lower() == ".svg":
        svg_data = file_path.read_text(encoding="utf-8", errors="replace")
        b64 = base64.b64encode(svg_data.encode()).decode()
        data_uri = f"data:image/svg+xml;base64,{b64}"
        return ProcessedFile(
            file_info=file_info,
            image_data=data_uri,
            image_dimensions=(0, 0),  # SVG dimensions are in the markup
        )

    # Raster images
    with PILImage.open(file_path) as img:
        width, height = img.size

    raw_bytes = file_path.read_bytes()
    b64 = base64.b64encode(raw_bytes).decode()
    data_uri = f"data:{mime_type};base64,{b64}"

    # Update the file_info with preview
    file_info.preview_url = data_uri

    return ProcessedFile(
        file_info=file_info,
        image_data=data_uri,
        image_dimensions=(width, height),
    )


def process_file(file_path: Path, file_info: UploadedFileInfo) -> ProcessedFile:
    """Route a file to the correct processor based on its type."""
    processors = {
        FileType.TEXT: process_text_file,
        FileType.PDF: process_pdf_file,
        FileType.MARKDOWN: process_markdown_file,
        FileType.IMAGE: process_image_file,
    }
    processor = processors.get(file_info.file_type, process_text_file)
    return processor(file_path, file_info)
