"""Content structuring + Table-of-Contents tools."""

import html as html_lib
import re

from app.agents.tool_context import get_context


def _slugify(title: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    return re.sub(r"[\s_]+", "-", slug).strip("-") or "section"


def structure_content(title: str, content_html: str, level: int = 2) -> str:
    """Create a styled HTML ``<section>`` for one part of the document.

    Call this for every major section and subsection. The agent should pass
    rich, semantic HTML in ``content_html`` (paragraphs, lists, blockquotes,
    inline emphasis). Tables, code, diagrams, callouts, and signal cards
    should be produced via their dedicated tools and inlined into
    ``content_html``.

    Args:
        title: Section heading text.
        content_html: Inner HTML for the section body.
        level: Heading level (2-6). Use 2 for top-level sections.
    """
    level = max(2, min(6, int(level)))
    slug = _slugify(title)

    rendered = (
        f'<section id="{slug}" class="doc-section doc-section-level-{level}">\n'
        f'  <h{level}>'
        f'<a href="#{slug}" class="section-anchor" aria-label="Link to {html_lib.escape(title)}">#</a> '
        f'{html_lib.escape(title)}'
        f'</h{level}>\n'
        f'  <div class="section-content">\n{content_html}\n  </div>\n'
        f'</section>'
    )

    ctx = get_context()
    ctx.sections.append({"title": title, "slug": slug, "level": level, "html": rendered})

    return rendered


def generate_toc() -> str:
    """Generate a nested Table-of-Contents from all previously created sections.

    Call this exactly ONCE, after every ``structure_content`` call.
    """
    sections = get_context().sections
    if not sections:
        return '<p class="toc-empty">No sections found.</p>'

    items: list[str] = []
    for s in sections:
        indent = "  " * (s["level"] - 2)
        items.append(
            f'{indent}<li><a href="#{s["slug"]}">{html_lib.escape(s["title"])}</a></li>'
        )
    return '<ul class="toc-list">\n' + "\n".join(items) + "\n</ul>"
