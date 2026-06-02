"""DocuForge Orchestrator — main AI agent powered by Google Antigravity SDK.

This module manages the lifecycle of the documentation generation agent,
including initialization, file ingestion, and streaming generation.
"""

from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator

from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.types import CapabilitiesConfig

from app.agents.tools.code_highlighter import highlight_code
from app.agents.tools.content_structurer import generate_toc, structure_content
from app.agents.tools.diagram_builder import build_diagram
from app.agents.tools.table_formatter import format_table
from app.config import settings
from app.models.schemas import (
    GenerateRequest,
    GeneratedDocument,
    GenerationStatus,
    GenerateProgress,
    ImagePlacementInfo,
)
from app.services.file_processor import ProcessedFile
from app.services.html_renderer import render_document


# ---------------------------------------------------------------------------
# System Instructions
# ---------------------------------------------------------------------------

SYSTEM_INSTRUCTIONS = """You are **DocuForge**, an expert documentation architect and technical writer.

Your mission is to transform raw input content (text, PDF extracts, Markdown, and metadata about images) into beautifully structured, semantic HTML documentation.

## Your Workflow

1. **Analyze** the provided content to understand its structure, topics, and key sections.
2. **Plan** the documentation structure — decide on sections, headings, and logical flow.
3. **Build** the documentation section by section using your tools:
   - Use `structure_content` for EVERY section — this creates properly formatted HTML sections with anchor links.
   - Use `format_table` when data is better presented as a table.
   - Use `highlight_code` for any code snippets, config files, or CLI commands.
   - Use `build_diagram` to create visual diagrams ONLY when diagrams are enabled.
   - Use `generate_toc` as the LAST step to build the Table of Contents.
4. **Review** the assembled output for coherence, completeness, and quality.

## Rules

1. **Always** use semantic HTML5 elements in your content (paragraphs, lists, blockquotes, etc.).
2. **Never** invent information — only document what is provided in the input.
3. **Structure first** — create a clear hierarchy with a Table of Contents.
4. When the `enable_diagrams` setting is `false`, do NOT call `build_diagram`.
5. When images are mentioned in the input metadata, note them but do NOT place them yourself — the system handles image placement separately.
6. Write in a professional, clear, concise technical writing style.
7. Use consistent formatting throughout the document.
8. Make content scannable with bullet points, numbered lists, and short paragraphs.
9. Add meaningful section titles that describe the content, not generic ones like "Section 1".
"""


# ---------------------------------------------------------------------------
# Task Store (in-memory for simplicity)
# ---------------------------------------------------------------------------

class TaskStore:
    """Simple in-memory store for generation tasks."""

    def __init__(self) -> None:
        self._tasks: dict[str, dict] = {}

    def create(self, task_id: str, request: GenerateRequest) -> dict:
        task = {
            "task_id": task_id,
            "request": request,
            "status": GenerationStatus.PENDING,
            "progress": 0.0,
            "current_step": "",
            "html_result": "",
            "sections_html": [],
            "events": asyncio.Queue(),
        }
        self._tasks[task_id] = task
        return task

    def get(self, task_id: str) -> dict | None:
        return self._tasks.get(task_id)

    def update(self, task_id: str, **kwargs) -> None:
        if task_id in self._tasks:
            self._tasks[task_id].update(kwargs)


task_store = TaskStore()


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

async def run_generation(
    task_id: str,
    request: GenerateRequest,
    processed_files: list[ProcessedFile],
    image_files: list[ProcessedFile],
) -> None:
    """Run the documentation generation agent in background.

    Sends progress events to the task's event queue for SSE streaming.
    """
    task = task_store.get(task_id)
    if not task:
        return

    events: asyncio.Queue = task["events"]

    async def send_progress(
        status: GenerationStatus,
        progress: float,
        step: str,
        message: str = "",
        html_preview: str | None = None,
        image_placement: ImagePlacementInfo | None = None,
    ) -> None:
        event = GenerateProgress(
            task_id=task_id,
            status=status,
            progress=progress,
            current_step=step,
            message=message,
            html_preview=html_preview,
            image_placement_required=image_placement,
        )
        await events.put(event)
        task_store.update(task_id, status=status, progress=progress, current_step=step)

    try:
        # ----- Step 1: Send initial progress -----
        await send_progress(
            GenerationStatus.PROCESSING, 0.05,
            "Initializing", "Setting up documentation agent..."
        )

        # ----- Step 2: Prepare input for the agent -----
        content_parts: list[str] = []
        for pf in processed_files:
            content_parts.append(
                f"--- File: {pf.file_info.filename} (type: {pf.file_info.file_type.value}) ---\n"
                f"{pf.text_content}\n"
            )

        # Note any images that were uploaded
        if image_files:
            img_notes = "\n".join(
                f"- Image: {img.file_info.filename} ({img.image_dimensions})"
                for img in image_files
            )
            content_parts.append(
                f"\n--- Uploaded Images ---\n{img_notes}\n"
                "Note: Images will be placed by the user via the image placement interface. "
                "Do NOT attempt to place images yourself.\n"
            )

        combined_content = "\n\n".join(content_parts)

        await send_progress(
            GenerationStatus.PROCESSING, 0.1,
            "Analyzing content", f"Processing {len(processed_files)} file(s)..."
        )

        # ----- Step 3: Build the prompt -----
        settings_description = (
            f"Document title: {request.title}\n"
            f"Theme: {request.theme.value}\n"
            f"Diagrams enabled: {request.enable_diagrams}\n"
            f"Table of Contents: {request.enable_toc}\n"
            f"Code highlighting: {request.enable_code_highlighting}\n"
        )

        if request.additional_instructions:
            settings_description += f"Additional instructions: {request.additional_instructions}\n"

        prompt = (
            f"Generate comprehensive HTML documentation from the following content.\n\n"
            f"## Settings\n{settings_description}\n\n"
            f"## Source Content\n{combined_content}\n\n"
            f"Use your tools (structure_content, format_table, highlight_code"
            f"{', build_diagram' if request.enable_diagrams else ''}) "
            f"to build each section. Call generate_toc at the end.\n\n"
            f"CRITICAL INSTRUCTION: Your final output MUST be the complete, assembled HTML document (including all generated sections and the TOC) concatenated together. Do not output conversational text or markdown code blocks, just the raw HTML."
        )

        await send_progress(
            GenerationStatus.PROCESSING, 0.15,
            "Starting agent", "Initializing AI documentation agent..."
        )

        # ----- Step 4: Configure and run the agent -----
        tools = [structure_content, format_table, highlight_code, generate_toc]
        if request.enable_diagrams:
            tools.append(build_diagram)

        config = LocalAgentConfig(
            model="gemini-3.1-pro",
            api_key=settings.GEMINI_API_KEY,
            system_instructions=SYSTEM_INSTRUCTIONS + "\n10. Take a deep breath and think step-by-step. Use your reasoning capabilities to carefully plan the document structure before finalizing the output.",
            tools=tools,
            capabilities=CapabilitiesConfig(
                enable_subagents=True,
            ),
        )

        async with Agent(config) as agent:
            await send_progress(
                GenerationStatus.PROCESSING, 0.2,
                "Generating", "Agent is analyzing and structuring content..."
            )

            response = await agent.chat(prompt)

            # Collect the full response
            full_response = ""
            async for chunk in response:
                full_response += chunk
                # Update progress incrementally
                progress = min(0.2 + (len(full_response) / max(len(combined_content), 1)) * 0.6, 0.85)
                await send_progress(
                    GenerationStatus.PROCESSING, progress,
                    "Building documentation", "Agent is generating sections..."
                )

        await send_progress(
            GenerationStatus.PROCESSING, 0.85,
            "Assembling HTML", "Combining sections into final document..."
        )

        # ----- Step 5: Handle image placement prompts -----
        if image_files:
            for img in image_files:
                await send_progress(
                    GenerationStatus.AWAITING_INPUT, 0.87,
                    "Image placement",
                    f"Where should '{img.file_info.filename}' be placed?",
                    image_placement=ImagePlacementInfo(
                        image_id=img.file_info.file_id,
                        filename=img.file_info.filename,
                        preview_url=img.image_data or "",
                        available_sections=[],  # Will be populated from agent state
                    ),
                )
                # Wait for image placement response (with timeout)
                # In production, this would wait for the user's placement choice
                # For now, the frontend sends the placement via the API endpoint
                await asyncio.sleep(0.5)

        # ----- Step 6: Render final HTML -----
        await send_progress(
            GenerationStatus.PROCESSING, 0.9,
            "Rendering HTML", "Applying theme and building final document..."
        )

        # Clean up markdown code blocks if the LLM wrapped the output
        final_body = full_response.strip()
        if final_body.startswith("```"):
            lines = final_body.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            final_body = "\n".join(lines)

        doc = GeneratedDocument(
            task_id=task_id,
            title=request.title,
            theme=request.theme,
            full_html=final_body,
            word_count=len(final_body.split()),
            diagram_count=final_body.count("mermaid"),
            section_count=final_body.count("<section"),
        )

        final_html = render_document(doc)

        # Save the output
        from app.services.html_renderer import save_document
        output_filename = f"docuforge_{task_id[:8]}.html"
        save_document(final_html, output_filename)

        task_store.update(task_id, html_result=final_html)

        await send_progress(
            GenerationStatus.COMPLETE, 1.0,
            "Complete", "Documentation generated successfully!",
            html_preview=final_html,
        )

    except Exception as e:
        await send_progress(
            GenerationStatus.ERROR, 0.0,
            "Error", f"Generation failed: {str(e)}"
        )


async def stream_events(task_id: str) -> AsyncGenerator[str, None]:
    """Yield SSE-formatted events for a generation task."""
    task = task_store.get(task_id)
    if not task:
        yield f"data: {json.dumps({'error': 'Task not found'})}\n\n"
        return

    events: asyncio.Queue = task["events"]

    while True:
        try:
            event: GenerateProgress = await asyncio.wait_for(events.get(), timeout=60.0)
            yield f"data: {event.model_dump_json()}\n\n"

            if event.status in (GenerationStatus.COMPLETE, GenerationStatus.ERROR):
                break
        except asyncio.TimeoutError:
            # Send keepalive
            yield ": keepalive\n\n"
