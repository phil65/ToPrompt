from __future__ import annotations

from importlib.metadata import version

__version__ = version("toprompt")

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
