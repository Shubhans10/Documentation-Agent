"""HTML table tool."""

import html as html_lib

from app.agents.tool_context import get_context


def format_table(headers: list[str], rows: list[list[str]], caption: str = "") -> str:
    """Render structured tabular data as a styled HTML table.

    Args:
        headers: Column header labels.
        rows: List of rows; each row must have ``len(headers)`` cells.
              Cells may contain inline HTML (``<code>``, ``<strong>``, tag
              pills, etc.).
        caption: Optional caption above the table.
    """
    get_context().tables.append({"headers": headers, "rows": rows, "caption": caption})

    header_cells = "".join(f"<th>{html_lib.escape(str(h))}</th>" for h in headers)
    body_rows = "".join(
        "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
        for row in rows
    )
    caption_html = (
        f"<caption>{html_lib.escape(caption)}</caption>" if caption else ""
    )

    return (
        '<figure class="table-container">\n'
        '  <table>\n'
        f'    {caption_html}\n'
        f'    <thead><tr>{header_cells}</tr></thead>\n'
        f'    <tbody>{body_rows}</tbody>\n'
        '  </table>\n'
        '</figure>'
    )
