"""ToPrompt: Convert python objects to LLM-friendly descriptions"""

from __future__ import annotations

from importlib.metadata import version

__version__ = version("toprompt")
__title__ = "ToPrompt"
__description__ = "Convert python objects to LLM-friendly descriptions"
__author__ = "Philipp Temminghoff"
__author_email__ = "philipptemminghoff@googlemail.com"
__copyright__ = "Copyright (c) 2025 Philipp Temminghoff"
__license__ = "MIT"
__url__ = "https://github.com/phil65/toprompt"

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
