"""Per-task shared state for tool calls.

The `google-genai` SDK invokes tool functions as plain Python callables — it
does not pass a context object the way the (fictional) Antigravity SDK did.
We therefore stash the active :class:`TaskContext` in a
:class:`contextvars.ContextVar` and have each tool read it via
:func:`get_context`.
"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, field


@dataclass
class TaskContext:
    """Mutable state accumulated by tool calls during a single generation."""

    sections: list[dict] = field(default_factory=list)
    diagrams: list[dict] = field(default_factory=list)
    tables: list[dict] = field(default_factory=list)
    code_blocks: list[dict] = field(default_factory=list)
    callouts: list[dict] = field(default_factory=list)


_current: ContextVar[TaskContext] = ContextVar("docuforge_task_context")


def set_context(ctx: TaskContext):
    """Bind ``ctx`` as the active task context. Returns a reset token."""
    return _current.set(ctx)


def reset_context(token) -> None:
    _current.reset(token)


def get_context() -> TaskContext:
    """Return the active task context (or a transient empty one)."""
    try:
        return _current.get()
    except LookupError:
        # Allows tools to be called outside a request (tests, REPL) without crashing.
        return TaskContext()
