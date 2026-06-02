"""Table formatter tool — creates styled HTML tables from structured data."""

from __future__ import annotations

from google.antigravity import ToolContext


def format_table(
    headers: list[str],
    rows: list[list[str]],
    caption: str,
    ctx: ToolContext,
) -> str:
    """Formats structured data into a styled HTML table.

    Use this tool when the content contains data that would be clearer as a
    table — comparisons, specifications, feature lists, API references, etc.

    Args:
        headers: Column header labels, e.g. ["Name", "Type", "Description"].
        rows: A list of rows, where each row is a list of cell values.
              Each row must have the same number of items as headers.
        caption: A short caption for the table.
        ctx: Tool context for state management (injected automatically).
    """
    # Track tables in context state
    tables = ctx.get_state("tables", [])
    tables.append({"headers": headers, "rows": rows, "caption": caption})
    ctx.set_state("tables", tables)

    # Build HTML
    header_cells = "".join(f"<th>{h}</th>" for h in headers)
    body_rows: list[str] = []
    for row in rows:
        cells = "".join(f"<td>{cell}</td>" for cell in row)
        body_rows.append(f"<tr>{cells}</tr>")

    html = f"""<figure class="table-container">
    <table>
        <caption>{caption}</caption>
        <thead><tr>{header_cells}</tr></thead>
        <tbody>{''.join(body_rows)}</tbody>
    </table>
</figure>"""

    return html
