from __future__ import annotations

try:
    from importlib.metadata import version
except ImportError:
    from importlib_metadata import version  # Python < 3.8

try:
    __version__ = version("toprompt")
except Exception:
    __version__ = "unknown"

from toprompt.to_prompt import (
    Template,
    to_prompt,
    AnyPromptType,
    render_prompt,
    PromptConvertible,
    PromptTypeConvertible,
)

__all__ = [
    "AnyPromptType",
    "PromptConvertible",
    "PromptTypeConvertible",
    "Template",
    "__version__",
    "render_prompt",
    "to_prompt",
]
