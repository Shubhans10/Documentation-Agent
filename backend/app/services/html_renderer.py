"""HTML renderer — assembles the final self-contained HTML document from Jinja2 templates."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.config import settings
from app.models.schemas import GeneratedDocument, Theme


# Jinja2 environment pointing at the templates directory
_env = Environment(
    loader=FileSystemLoader(str(settings.TEMPLATES_DIR)),
    autoescape=True,
)


# ---------------------------------------------------------------------------
# Theme CSS
# ---------------------------------------------------------------------------

THEME_STYLES: dict[Theme, str] = {
    Theme.MODERN_DARK: """
        :root {
            --bg-primary: #0a0e1a;
            --bg-secondary: #111827;
            --bg-card: rgba(17, 24, 39, 0.8);
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --accent: #3b82f6;
            --accent-hover: #60a5fa;
            --accent-glow: rgba(59, 130, 246, 0.3);
            --border: rgba(148, 163, 184, 0.1);
            --code-bg: #1e293b;
            --table-stripe: rgba(59, 130, 246, 0.05);
            --shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        }
        body { background: var(--bg-primary); color: var(--text-primary); }
    """,
    Theme.CLEAN_LIGHT: """
        :root {
            --bg-primary: #f8fafc;
            --bg-secondary: #ffffff;
            --bg-card: rgba(255, 255, 255, 0.9);
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --accent: #2563eb;
            --accent-hover: #1d4ed8;
            --accent-glow: rgba(37, 99, 235, 0.15);
            --border: rgba(15, 23, 42, 0.08);
            --code-bg: #f1f5f9;
            --table-stripe: rgba(37, 99, 235, 0.03);
            --shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
        }
        body { background: var(--bg-primary); color: var(--text-primary); }
    """,
    Theme.TECHNICAL_BLUEPRINT: """
        :root {
            --bg-primary: #0c1222;
            --bg-secondary: #131d36;
            --bg-card: rgba(19, 29, 54, 0.85);
            --text-primary: #c8d6e5;
            --text-secondary: #8395a7;
            --accent: #00d2d3;
            --accent-hover: #01a3a4;
            --accent-glow: rgba(0, 210, 211, 0.25);
            --border: rgba(200, 214, 229, 0.08);
            --code-bg: #0a1628;
            --table-stripe: rgba(0, 210, 211, 0.04);
            --shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
        }
        body { background: var(--bg-primary); color: var(--text-primary); }
    """,
}


def render_document(doc: GeneratedDocument) -> str:
    """Render the final self-contained HTML document."""
    template = _env.get_template("doc_base.html")
    theme_css = THEME_STYLES.get(doc.theme, THEME_STYLES[Theme.MODERN_DARK])

    return template.render(
        title=doc.title,
        theme_css=theme_css,
        toc_html=doc.toc_html,
        sections=doc.sections,
        full_html=doc.full_html,
        word_count=doc.word_count,
        diagram_count=doc.diagram_count,
        section_count=doc.section_count,
    )


def save_document(html: str, filename: str) -> Path:
    """Save rendered HTML to the output directory and return the path."""
    output_path = settings.OUTPUT_DIR / filename
    output_path.write_text(html, encoding="utf-8")
    return output_path
