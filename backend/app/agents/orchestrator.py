"""DocuForge orchestrator — runs a Gemini agent via the unified `google-genai`
SDK with automatic function calling against the documentation tools.

Auth is handled by :mod:`app.services.llm_client`, which transparently uses
either an API key (Gemini Developer API) or a GCP service-account JSON
(Vertex AI).
"""

from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator

from google.genai import types

from app.agents.tool_context import TaskContext, reset_context, set_context
from app.agents.tools.code_highlighter import highlight_code
from app.agents.tools.content_structurer import generate_toc, structure_content
from app.agents.tools.diagram_builder import build_diagram
from app.agents.tools.rich_primitives import (
    build_callout,
    build_decision_tree,
    build_formula_block,
    build_principle,
    build_signal_card,
    build_tag,
)
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
from app.services.html_renderer import render_document, save_document
from app.services.llm_client import build_client


# ---------------------------------------------------------------------------
# System Instructions
# ---------------------------------------------------------------------------

SYSTEM_INSTRUCTIONS = r"""You are **DocuForge**, an expert documentation architect and technical writer.

Your job is to convert raw input (text, PDF extracts, Markdown, image metadata) into ONE polished, semantic HTML document. Reply with the RAW HTML only — no commentary, no markdown fences, no <html>/<head>/<body> wrapper (those are added by the host).

# Document skeleton

Emit, in this exact order:

1. (If a Table of Contents is requested) `<nav class="toc"><h2>Contents</h2><ul class="toc-list">…</ul></nav>`
   - One `<li><a href="#slug">Title</a></li>` per top-level section.
2. One `<section id="slug" class="doc-section doc-section-level-2">` per top-level section, in reading order.
   - First child must be `<h2><a href="#slug" class="section-anchor" aria-label="Link to Title">#</a> Title</h2>`
   - Followed by `<div class="section-content"> … rich body HTML … </div>`
   - Sub-sections use `doc-section-level-3` and `<h3>`, etc.
   - `slug` is lowercase-kebab-case derived from the title.

# Rich primitives (USE THESE GENEROUSLY — they are the visual vocabulary)

Callout (rule | warn | info | change | tbd):
  <div class="callout callout-{variant}">
    <div class="callout-title">{title}</div>
    <div class="callout-body">{body_html}</div>
  </div>

Signal card (variant: strong | neutral | weak | info | primary | secondary; number is optional badge text):
  <div class="signal-card signal-{variant}">
    <div class="sig-num">{number}</div>
    <div class="sig-title">{title}</div>
    <div class="sig-body">{body_html}</div>
  </div>

Tag (variant: primary | secondary | strong | neutral | weak | info | warn | success | danger):
  <span class="tag tag-{variant}">{label}</span>
  Use inside table cells and inline prose for categorical badges (STRONG / NEUTRAL / WEAK, status labels, etc.).

Principle (numbered governing row):
  <div class="principle">
    <div class="principle-num">{number}</div>
    <div class="principle-body">
      <div class="principle-title">{title}</div>
      <div class="principle-text">{body_html}</div>
    </div>
  </div>

Formula block:
  <div class="formula-block">
    {formula}
    <div class="formula-note">{note}</div>   <!-- omit if no note -->
  </div>

Decision tree (variants: gate | check | outcome-long | outcome-short | outcome-consolidate | outcome-exit | tiebreaker):
  <div class="tree-container">
    <div class="tree-node gate"><strong>Start</strong><div class="tree-body">…</div></div>
    <div class="tree-arrow">&darr;</div>
    <div class="tree-label">if condition</div>     <!-- optional -->
    <div class="tree-node check"><strong>Next step</strong><div class="tree-body">…</div></div>
    …
  </div>

Table (use freely; wrap in a figure for captions):
  <figure class="table-wrap">
    <table class="data-table">
      <thead><tr><th>Header A</th><th>Header B</th></tr></thead>
      <tbody>
        <tr><td>…</td><td><span class="tag tag-strong">STRONG</span></td></tr>
      </tbody>
    </table>
    <figcaption>{caption}</figcaption>   <!-- optional -->
  </figure>

Code block (only if code highlighting is enabled — set language- class for Prism.js):
  <figure class="code-block">
    <div class="code-block-header">{title or language}</div>
    <pre><code class="language-{language}">{escaped_code}</code></pre>
  </figure>

Mermaid diagram (ONLY if diagrams are enabled; types: flowchart | sequence | state | class | er):
  <figure class="diagram diagram-{diagram_type}">
    <pre class="mermaid">{mermaid_code}</pre>
    <figcaption>{caption}</figcaption>   <!-- optional -->
  </figure>
  CRITICAL: inside `<pre class="mermaid">`, write Mermaid syntax LITERALLY. Do NOT HTML-escape it.
  Use `-->`  NOT  `--&gt;`. Use `<` and `>` as-is in arrows and labels. Do NOT wrap the code in markdown fences.

# Style rules

- Mirror professional technical-spec layout: short paragraphs, scannable lists, dense tables, named principles, callouts for rules/warnings/changes, signal cards for individual concepts.
- Use callouts: `rule` for normative statements, `warn` for cautions, `change` for changelog notes, `info` for tips, `tbd` for open items.
- Use signal cards whenever describing one named signal / principle / topic. Number them sequentially when they form a series.
- Use tags inside table cells and inline prose to badge categorical values.
- Escape user-supplied text — never inject raw `<` `>` `&` from the source content into HTML attributes or text nodes; convert to entities.
- Never invent facts. Only document what the input actually contains.
- Diagrams: ONLY when diagrams are enabled in settings. Prefer flowchart / sequence / state.
- Images: do NOT place them — the host application handles image placement separately.
- Do NOT wrap the answer in markdown fences. Do NOT add commentary before or after the HTML.

Plan the structure first, then write the document in one pass.
"""


# ---------------------------------------------------------------------------
# Task Store
# ---------------------------------------------------------------------------

class TaskStore:
    """In-memory store for generation tasks."""

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
    """Run the documentation generation agent in the background."""
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

    ctx_token = None
    try:
        await send_progress(
            GenerationStatus.PROCESSING, 0.05,
            "Initializing", "Setting up documentation agent...",
        )

        # ----- 1. Assemble source content ---------------------------------
        parts: list[str] = []
        for pf in processed_files:
            parts.append(
                f"--- File: {pf.file_info.filename} "
                f"(type: {pf.file_info.file_type.value}) ---\n{pf.text_content}\n"
            )
        if image_files:
            img_notes = "\n".join(
                f"- {img.file_info.filename} ({img.image_dimensions})"
                for img in image_files
            )
            parts.append(
                f"\n--- Uploaded Images ---\n{img_notes}\n"
                "Note: image placement is handled by the host application.\n"
            )
        source_content = "\n\n".join(parts)

        await send_progress(
            GenerationStatus.PROCESSING, 0.15,
            "Analysing content",
            f"Processing {len(processed_files)} file(s) and {len(image_files)} image(s)...",
        )

        # ----- 2. Build prompt --------------------------------------------
        settings_block = (
            f"Document title: {request.title}\n"
            f"Theme: {request.theme.value}\n"
            f"Diagrams enabled: {request.enable_diagrams}\n"
            f"Table of contents: {request.enable_toc}\n"
            f"Code highlighting: {request.enable_code_highlighting}\n"
        )
        if request.additional_instructions:
            settings_block += f"Additional instructions: {request.additional_instructions}\n"

        prompt = (
            "Build a polished HTML document from the source below.\n\n"
            f"## Settings\n{settings_block}\n"
            f"## Source content\n{source_content}\n\n"
            "Emit the complete document as ONE block of raw HTML following the "
            "skeleton and primitive patterns described in the system instructions. "
            "No commentary. No markdown fences."
        )

        # ----- 3. Bind task context (kept for downstream stats) -----------
        task_ctx = TaskContext()
        ctx_token = set_context(task_ctx)

        # ----- 4. Run the model ------------------------------------------
        await send_progress(
            GenerationStatus.PROCESSING, 0.25,
            "Generating", "Gemini is writing the document...",
        )

        client = build_client()
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTIONS,
            temperature=0.4,
            max_output_tokens=32768,
        )

        response = await client.aio.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=config,
        )

        # Robust text extraction: walk every candidate part and concatenate
        # text segments. `response.text` can return None when text coexists
        # with function_call or thought parts on gemini-2.5-pro.
        def _collect_text(resp) -> str:
            chunks: list[str] = []
            for cand in getattr(resp, "candidates", None) or []:
                content = getattr(cand, "content", None)
                for part in getattr(content, "parts", None) or []:
                    txt = getattr(part, "text", None)
                    if txt and not getattr(part, "thought", False):
                        chunks.append(txt)
            return "".join(chunks)

        full_response = (response.text or _collect_text(response) or "").strip()

        try:
            finish_reason = response.candidates[0].finish_reason
        except Exception:
            finish_reason = None
        print(
            f"[orchestrator] task={task_id[:8]} finish_reason={finish_reason} "
            f"text_len={len(full_response)}",
            flush=True,
        )

        if not full_response:
            raise RuntimeError(
                f"Model returned no content (finish_reason={finish_reason}). "
                "Check backend logs."
            )

        # ----- 5. Strip stray markdown fences ----------------------------
        body = full_response
        if body.startswith("```"):
            lines = body.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            body = "\n".join(lines)

        # ----- 6. Derive stats from the produced HTML --------------------
        import re as _re
        import html as _html

        # Mermaid: the model often HTML-escapes arrows (`--&gt;`, `&lt;`) inside
        # diagram blocks, which breaks mermaid.js parsing. Un-escape the content
        # of any element with class "mermaid".
        def _unescape_mermaid(match: "_re.Match[str]") -> str:
            opening, inner, closing = match.group(1), match.group(2), match.group(3)
            return f"{opening}{_html.unescape(inner)}{closing}"

        body = _re.sub(
            r'(<(?:pre|div)[^>]*class="[^"]*\bmermaid\b[^"]*"[^>]*>)(.*?)(</(?:pre|div)>)',
            _unescape_mermaid,
            body,
            flags=_re.DOTALL,
        )

        section_titles = _re.findall(
            r'<section[^>]*class="[^"]*doc-section-level-2[^"]*"[^>]*>\s*<h2[^>]*>(?:\s*<a[^>]*>[^<]*</a>)?\s*([^<]+)',
            body,
        )
        section_count = len(section_titles) or len(_re.findall(r"<section\b", body))
        diagram_count = len(_re.findall(r'class="mermaid"', body))

        await send_progress(
            GenerationStatus.PROCESSING, 0.85,
            "Assembling HTML",
            f"{section_count} section(s), {diagram_count} diagram(s).",
        )

        # ----- 7. Image placement prompts (UI-driven) --------------------
        for img in image_files:
            await send_progress(
                GenerationStatus.AWAITING_INPUT, 0.87,
                "Image placement",
                f"Where should '{img.file_info.filename}' be placed?",
                image_placement=ImagePlacementInfo(
                    image_id=img.file_info.file_id,
                    filename=img.file_info.filename,
                    preview_url=img.image_data or "",
                    available_sections=[t.strip() for t in section_titles],
                ),
            )
            await asyncio.sleep(0.1)

        # ----- 8. Render final HTML with theme chrome --------------------
        doc = GeneratedDocument(
            task_id=task_id,
            title=request.title,
            theme=request.theme,
            full_html=body,
            word_count=len(body.split()),
            diagram_count=diagram_count,
            section_count=section_count,
        )
        final_html = render_document(doc)
        save_document(final_html, f"docuforge_{task_id[:8]}.html")
        task_store.update(task_id, html_result=final_html)

        await send_progress(
            GenerationStatus.COMPLETE, 1.0,
            "Complete", "Documentation generated successfully.",
            html_preview=final_html,
        )

    except Exception as e:
        await send_progress(
            GenerationStatus.ERROR, 0.0,
            "Error", f"Generation failed: {e}",
        )
    finally:
        if ctx_token is not None:
            reset_context(ctx_token)


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
            yield ": keepalive\n\n"
