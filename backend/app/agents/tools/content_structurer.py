"""Content structurer tool — organizes content into semantic HTML5 sections with navigation."""

from __future__ import annotations

import html as html_lib
import re

from google.antigravity import ToolContext


def structure_content(
    title: str,
    content_html: str,
    level: int,
    ctx: ToolContext,
) -> str:
    """Creates a structured HTML section with proper heading hierarchy.

    Use this tool to organize the documentation into logical sections.
    Call it for each major section of the document. The orchestrator should
    call this multiple times to build the complete document structure.

    Args:
        title: The section title.
        content_html: The HTML content for this section. Can include paragraphs,
                      lists, blockquotes, and other HTML elements.
        level: The heading level (2-6). Use 2 for top-level sections,
               3 for subsections, etc.
        ctx: Tool context for state management (injected automatically).
    """
    level = max(2, min(6, level))  # Clamp to valid heading levels

    # Generate a URL-safe slug for the section ID
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")

    # Track sections for TOC generation
    sections = ctx.get_state("sections", [])
    section_entry = {
        "title": title,
        "slug": slug,
        "level": level,
        "index": len(sections),
    }
    sections.append(section_entry)
    ctx.set_state("sections", sections)

    # Build HTML
    html = f"""<section id="{slug}" class="doc-section doc-section-level-{level}">
    <h{level}>
        <a href="#{slug}" class="section-anchor" aria-label="Link to {html_lib.escape(title)}">#</a>
        {html_lib.escape(title)}
    </h{level}>
    <div class="section-content">
        {content_html}
    </div>
</section>"""

    return html


def generate_toc(ctx: ToolContext) -> str:
    """Generates a Table of Contents HTML from all structured sections.

    Call this AFTER all sections have been created using structure_content.
    It reads the sections from the tool context state and builds a nested list.

    Args:
        ctx: Tool context for state management (injected automatically).
    """
    sections = ctx.get_state("sections", [])
    if not sections:
        return "<p>No sections found.</p>"

    items: list[str] = []
    for section in sections:
        indent = "  " * (section["level"] - 2)
        items.append(
            f'{indent}<li><a href="#{section["slug"]}">{html_lib.escape(section["title"])}</a></li>'
        )

    return f'<ul class="toc-list">\n{"chr(10)".join(items)}\n</ul>'
