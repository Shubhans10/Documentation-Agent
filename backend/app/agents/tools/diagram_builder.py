"""Diagram builder tool — generates Mermaid.js diagram markup from descriptions."""

from __future__ import annotations

from google.antigravity import ToolContext


SUPPORTED_DIAGRAM_TYPES = {
    "flowchart",
    "sequence",
    "class",
    "er",
    "gantt",
    "pie",
    "state",
    "mindmap",
}


def build_diagram(diagram_type: str, mermaid_code: str, caption: str, ctx: ToolContext) -> str:
    """Creates a Mermaid.js diagram and returns it as an HTML snippet.

    Use this tool when the user has enabled diagrams and the content would
    benefit from a visual representation such as a flowchart, sequence diagram,
    class diagram, entity-relationship diagram, Gantt chart, or pie chart.

    Args:
        diagram_type: The type of diagram — one of: flowchart, sequence, class,
                      er, gantt, pie, state, mindmap.
        mermaid_code: Valid Mermaid.js syntax for the diagram. Do NOT wrap it in
                      triple backticks — just the raw Mermaid code.
        caption: A short caption describing what the diagram shows.
        ctx: Tool context for state management (injected automatically).
    """
    if diagram_type not in SUPPORTED_DIAGRAM_TYPES:
        return f"Error: Unsupported diagram type '{diagram_type}'. Supported types: {', '.join(sorted(SUPPORTED_DIAGRAM_TYPES))}"

    # Track diagrams in context state
    diagrams = ctx.get_state("diagrams", [])
    diagram_entry = {
        "type": diagram_type,
        "code": mermaid_code,
        "caption": caption,
    }
    diagrams.append(diagram_entry)
    ctx.set_state("diagrams", diagrams)

    # Return HTML snippet
    html = f"""<div class="diagram-container">
    <div class="mermaid">
{mermaid_code}
    </div>
    <p class="doc-image-caption">{caption}</p>
</div>"""

    return html
