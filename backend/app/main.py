"""DocuForge — FastAPI application with file upload, SSE streaming, and generation endpoints."""

from __future__ import annotations

import asyncio
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse

from app.agents.orchestrator import run_generation, stream_events, task_store
from app.config import settings
from app.models.schemas import (
    ChatMessage,
    ChatResponse,
    FileType,
    GenerateRequest,
    ImagePlacementRequest,
    UploadedFileInfo,
    UploadResponse,
)
from app.services.file_processor import ProcessedFile, detect_file_type, process_file
from app.services.llm_client import describe_auth


# ---------------------------------------------------------------------------
# In-memory file store
# ---------------------------------------------------------------------------

_uploaded_files: dict[str, tuple[UploadedFileInfo, Path]] = {}
_processed_cache: dict[str, ProcessedFile] = {}


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Validate settings on startup."""
    settings.validate()
    yield
    # Cleanup on shutdown (nothing to clean currently)


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="DocuForge API",
    description="AI-powered documentation generation agent",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "DocuForge API",
        "auth": describe_auth(),
    }


# ---------------------------------------------------------------------------
# File Upload
# ---------------------------------------------------------------------------

@app.post("/api/upload", response_model=UploadResponse)
async def upload_files(files: list[UploadFile] = File(...)):
    """Upload one or more files for documentation generation."""
    uploaded: list[UploadedFileInfo] = []
    images_detected: list[UploadedFileInfo] = []

    for upload_file in files:
        if not upload_file.filename:
            continue

        # Validate extension
        ext = Path(upload_file.filename).suffix.lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {ext}. Allowed: {', '.join(sorted(settings.ALLOWED_EXTENSIONS))}",
            )

        # Read and validate size
        content = await upload_file.read()
        if len(content) > settings.MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File '{upload_file.filename}' exceeds maximum size of {settings.MAX_FILE_SIZE_MB}MB",
            )

        # Detect file type
        file_type = detect_file_type(upload_file.filename)
        is_image = file_type == FileType.IMAGE

        # Create file info
        file_info = UploadedFileInfo(
            filename=upload_file.filename,
            file_type=file_type,
            size_bytes=len(content),
            is_image=is_image,
        )

        # Save to upload directory
        file_path = settings.UPLOAD_DIR / f"{file_info.file_id}{ext}"
        file_path.write_bytes(content)

        # Process immediately to get metadata
        processed = process_file(file_path, file_info)
        _uploaded_files[file_info.file_id] = (file_info, file_path)
        _processed_cache[file_info.file_id] = processed

        # Update preview for images
        if is_image and processed.image_data:
            file_info.preview_url = processed.image_data

        uploaded.append(file_info)
        if is_image:
            images_detected.append(file_info)

    return UploadResponse(
        files=uploaded,
        images_detected=images_detected,
        message=f"Uploaded {len(uploaded)} file(s), {len(images_detected)} image(s) detected",
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

@app.post("/api/generate")
async def start_generation(request: GenerateRequest):
    """Start documentation generation. Returns a task_id for SSE streaming."""
    # Validate file IDs
    processed_files: list[ProcessedFile] = []
    image_files: list[ProcessedFile] = []

    for file_id in request.file_ids:
        if file_id not in _processed_cache:
            raise HTTPException(status_code=404, detail=f"File {file_id} not found. Upload it first.")
        pf = _processed_cache[file_id]
        if pf.file_info.is_image:
            image_files.append(pf)
        else:
            processed_files.append(pf)

    if not processed_files and not image_files:
        raise HTTPException(status_code=400, detail="No valid files to generate documentation from.")

    # Create task
    task_id = str(uuid.uuid4())
    task_store.create(task_id, request)

    # Launch generation in background
    asyncio.create_task(
        run_generation(task_id, request, processed_files, image_files)
    )

    return {"task_id": task_id, "message": "Generation started", "stream_url": f"/api/generate/{task_id}/stream"}


@app.get("/api/generate/{task_id}/stream")
async def generation_stream(task_id: str):
    """SSE stream for generation progress."""
    task = task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return StreamingResponse(
        stream_events(task_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Image Placement
# ---------------------------------------------------------------------------

@app.post("/api/image-placement")
async def set_image_placement(request: ImagePlacementRequest):
    """Set the placement for a detected image."""
    task = task_store.get(request.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Store placement decision — the orchestrator will pick this up
    placements = task.get("image_placements", {})
    placements[request.image_id] = {
        "placement": request.placement.value,
        "section_id": request.section_id,
    }
    task_store.update(request.task_id, image_placements=placements)

    return {"message": f"Image placement set to '{request.placement.value}'"}


# ---------------------------------------------------------------------------
# Preview & Export
# ---------------------------------------------------------------------------

@app.get("/api/preview/{task_id}")
async def get_preview(task_id: str):
    """Get the current HTML preview for a task."""
    task = task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    html = task.get("html_result", "")
    if not html:
        return {"status": task.get("status", "pending"), "html": None}

    return HTMLResponse(content=html)


@app.get("/api/export/{task_id}")
async def export_document(task_id: str):
    """Download the generated HTML document."""
    task = task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    html = task.get("html_result", "")
    if not html:
        raise HTTPException(status_code=400, detail="Document not ready yet")

    # Find the output file
    output_filename = f"docuforge_{task_id[:8]}.html"
    output_path = settings.OUTPUT_DIR / output_filename

    if output_path.exists():
        return FileResponse(
            path=str(output_path),
            filename=output_filename,
            media_type="text/html",
        )

    # Fallback: return HTML directly
    return HTMLResponse(
        content=html,
        headers={"Content-Disposition": f"attachment; filename={output_filename}"},
    )


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_agent(message: ChatMessage):
    """Send an additional message to the agent during/after generation."""
    task = task_store.get(message.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # For now, return a placeholder — in a full implementation,
    # this would forward the message to the running agent conversation
    return ChatResponse(
        message="Message received. The agent will incorporate your feedback in the next generation.",
        updated_preview=False,
    )
