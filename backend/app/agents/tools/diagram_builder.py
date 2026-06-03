"""Mermaid diagram tool."""

import html as html_lib

from app.agents.tool_context import get_context


SUPPORTED_DIAGRAM_TYPES = {
    "flowchart", "sequence", "class", "er", "gantt",
    "pie", "state", "mindmap", "journey",
}


def build_diagram(diagram_type: str, mermaid_code: str, caption: str = "") -> str:
    """Render a Mermaid.js diagram as an HTML snippet.

    Use ONLY when ``enable_diagrams`` is true.

    Args:
        diagram_type: One of flowchart, sequence, class, er, gantt, pie, state,
                      mindmap, journey.
        mermaid_code: Raw Mermaid syntax (no triple backticks).
        caption: Short caption shown beneath the diagram.
    """
    if diagram_type not in SUPPORTED_DIAGRAM_TYPES:
        return (
            f"<!-- Unsupported diagram type '{diagram_type}'. "
            f"Supported: {sorted(SUPPORTED_DIAGRAM_TYPES)} -->"
        )

    get_context().diagrams.append(
        {"type": diagram_type, "code": mermaid_code, "caption": caption}
    )

    caption_html = (
        f'<figcaption class="diagram-caption">{html_lib.escape(caption)}</figcaption>'
        if caption else ""
    )
    return (
        '<figure class="diagram-container">\n'
        f'  <div class="mermaid">\n{mermaid_code}\n  </div>\n'
        f'  {caption_html}\n'
        '</figure>'
    )
