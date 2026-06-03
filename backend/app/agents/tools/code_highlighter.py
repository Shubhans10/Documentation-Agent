"""Syntax-highlighted code block tool."""

import html as html_lib

from app.agents.tool_context import get_context


LANGUAGE_MAP: dict[str, str] = {
    "py": "python", "js": "javascript", "ts": "typescript",
    "rb": "ruby", "sh": "bash", "shell": "bash",
    "yml": "yaml", "md": "markdown", "cs": "csharp",
    "c++": "cpp", "objective-c": "objectivec", "objc": "objectivec",
}


def highlight_code(code: str, language: str, title: str = "") -> str:
    """Wrap a code snippet in a Prism.js-compatible block.

    Args:
        code: Raw source.
        language: Language id (``python``, ``bash``, ``json`` …).
        title: Optional filename/title shown in the header.
    """
    lang = LANGUAGE_MAP.get(language.lower(), language.lower())
    get_context().code_blocks.append({"language": lang, "title": title})

    escaped = html_lib.escape(code)
    title_html = (
        f'<div class="code-block-header">'
        f'<span class="code-block-title">{html_lib.escape(title)}</span>'
        f'<span class="code-block-lang">{lang}</span>'
        f'</div>'
    ) if title else ""

    return (
        f'<div class="code-block">\n'
        f'  {title_html}\n'
        f'  <pre><code class="language-{lang}">{escaped}</code></pre>\n'
        f'</div>'
    )
