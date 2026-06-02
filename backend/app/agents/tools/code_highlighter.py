"""Code highlighter tool — wraps code snippets in Prism.js-compatible HTML blocks."""

from __future__ import annotations

import html as html_lib

from google.antigravity import ToolContext


# Language aliases for Prism.js class names
LANGUAGE_MAP: dict[str, str] = {
    "py": "python",
    "js": "javascript",
    "ts": "typescript",
    "rb": "ruby",
    "sh": "bash",
    "shell": "bash",
    "yml": "yaml",
    "md": "markdown",
    "cs": "csharp",
    "cpp": "cpp",
    "c++": "cpp",
    "objective-c": "objectivec",
    "objc": "objectivec",
}


def highlight_code(
    code: str,
    language: str,
    title: str,
    ctx: ToolContext,
) -> str:
    """Wraps a code snippet in syntax-highlighted HTML using Prism.js classes.

    Use this tool when the content contains code snippets, configuration files,
    CLI commands, or any technical code that benefits from syntax highlighting.

    Args:
        code: The raw code string to highlight.
        language: The programming language (e.g. "python", "javascript", "bash",
                  "json", "yaml", "sql", "html", "css", etc.).
        title: A short title or filename for the code block (e.g. "main.py").
        ctx: Tool context for state management (injected automatically).
    """
    # Normalize language name
    lang = LANGUAGE_MAP.get(language.lower(), language.lower())

    # Track code blocks
    code_blocks = ctx.get_state("code_blocks", [])
    code_blocks.append({"language": lang, "title": title})
    ctx.set_state("code_blocks", code_blocks)

    # Escape HTML entities in the code
    escaped_code = html_lib.escape(code)

    html = f"""<div class="code-block">
    <div class="code-block-header">
        <span class="code-block-title">{html_lib.escape(title)}</span>
        <span class="code-block-lang">{lang}</span>
    </div>
    <pre><code class="language-{lang}">{escaped_code}</code></pre>
</div>"""

    return html
