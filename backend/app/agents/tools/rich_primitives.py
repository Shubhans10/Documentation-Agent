"""Rich semantic primitives that mirror the reference HTML samples.

These tools let the agent produce callout banners, signal/info cards,
coloured tag pills, decision-tree nodes, principle blocks, and boxed formulas
— the same building blocks used in the sample Recommendation-Agent and
LLM-Orchestration documents.

Each tool returns a self-contained HTML snippet that the agent should inline
into a section produced by :func:`structure_content`.
"""

import html as html_lib

from app.agents.tool_context import get_context


_CALLOUT_VARIANTS = {"rule", "warn", "info", "change", "tbd"}
_CARD_VARIANTS = {"strong", "neutral", "weak", "info", "primary", "secondary"}
_TAG_VARIANTS = {
    "primary", "secondary", "info", "strong", "neutral", "weak",
    "renew-long", "renew-short", "exit", "consolidate", "green",
    "amber", "red", "gray",
}
_TREE_NODE_VARIANTS = {"gate", "check", "outcome-long", "outcome-short",
                       "outcome-consolidate", "outcome-exit", "tiebreaker"}


def build_callout(variant: str, title: str, body_html: str) -> str:
    """A coloured callout banner (rule / warn / info / change / tbd).

    Args:
        variant: One of ``rule``, ``warn``, ``info``, ``change``, ``tbd``.
        title: Bold lead-in shown on the first line.
        body_html: HTML body — paragraphs, lists, inline tags.
    """
    variant = variant.lower()
    if variant not in _CALLOUT_VARIANTS:
        variant = "info"
    get_context().callouts.append({"variant": variant, "title": title})
    return (
        f'<div class="callout callout-{variant}">\n'
        f'  <strong>{html_lib.escape(title)}</strong>\n'
        f'  <div>{body_html}</div>\n'
        f'</div>'
    )


def build_signal_card(title: str, body_html: str, variant: str = "info",
                      number: str = "") -> str:
    """A bordered card that summarises a single signal / principle / topic.

    Args:
        title: Card heading.
        body_html: HTML body of the card.
        variant: ``strong`` | ``neutral`` | ``weak`` | ``info`` |
                 ``primary`` | ``secondary``.
        number: Optional small badge text (e.g. "1", "2a"). Empty for no badge.
    """
    variant = variant.lower()
    if variant not in _CARD_VARIANTS:
        variant = "info"
    badge = (
        f'<span class="sig-num sig-num-{variant}">{html_lib.escape(str(number))}</span>'
        if number else ""
    )
    return (
        f'<div class="signal-card card-{variant}">\n'
        f'  <h4>{badge}{html_lib.escape(title)}</h4>\n'
        f'  <div>{body_html}</div>\n'
        f'</div>'
    )


def build_tag(label: str, variant: str = "primary") -> str:
    """A small coloured pill / tag.

    Args:
        label: Visible text.
        variant: Colour: primary, secondary, info, strong, neutral, weak,
                 renew-long, renew-short, exit, consolidate, green, amber,
                 red, gray.
    """
    v = variant.lower()
    if v not in _TAG_VARIANTS:
        v = "primary"
    return f'<span class="tag tag-{v}">{html_lib.escape(label)}</span>'


def build_principle(number: int, title: str, body_html: str) -> str:
    """A numbered "governing principle" row (matches the reference layout)."""
    return (
        f'<div class="principle">\n'
        f'  <div class="num">{int(number)}</div>\n'
        f'  <div><strong>{html_lib.escape(title)}</strong>{body_html}</div>\n'
        f'</div>'
    )


def build_formula_block(formula: str, note: str = "") -> str:
    """A monospaced, left-bordered formula / definition block."""
    note_html = (
        f'<div class="formula-note">{html_lib.escape(note)}</div>' if note else ""
    )
    return (
        f'<div class="formula-block">{html_lib.escape(formula)}{note_html}</div>'
    )


def build_decision_tree(nodes_json: str) -> str:
    """Render a vertical decision-tree (like Section 7 of the sample).

    Args:
        nodes_json: JSON-encoded list of node objects. Each object has keys:
            ``variant`` (one of: ``gate``, ``check``, ``outcome-long``,
            ``outcome-short``, ``outcome-consolidate``, ``outcome-exit``,
            ``tiebreaker``), ``title``, ``body`` (HTML), and optional
            ``label`` (shown as arrow caption above the node).
            Example: ``'[{"variant":"gate","title":"Start","body":"..."}]'``.
    """
    import json as _json
    try:
        nodes = _json.loads(nodes_json) if isinstance(nodes_json, str) else nodes_json
    except Exception:
        nodes = []
    if not isinstance(nodes, list):
        nodes = []
    parts: list[str] = ['<div class="tree-container">']
    for i, n in enumerate(nodes):
        if not isinstance(n, dict):
            continue
        variant = (n.get("variant") or "check").lower()
        if variant not in _TREE_NODE_VARIANTS:
            variant = "check"
        if i > 0:
            label = n.get("label", "")
            label_html = (
                f'<div class="tree-label">{html_lib.escape(label)}</div>'
                if label else ""
            )
            parts.append(f'  <div class="tree-arrow">↓</div>\n  {label_html}')
        title = html_lib.escape(n.get("title", ""))
        body = n.get("body", "")
        parts.append(
            f'  <div class="tree-node {variant}"><strong>{title}</strong>'
            f'<div class="tree-body">{body}</div></div>'
        )
    parts.append("</div>")
    return "\n".join(parts)
