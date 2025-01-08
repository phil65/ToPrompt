from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable


if TYPE_CHECKING:
    from collections.abc import Sequence


class PromptMessage(Protocol):
    """Protocol for prompt messages."""

    def get_text_content(self) -> str: ...


@runtime_checkable
class BasePromptProtocol(Protocol):
    """Protocol for base prompt interface."""

    messages: Sequence[PromptMessage]

    def get_messages(self) -> Sequence[PromptMessage]: ...

    def validate_arguments(self, provided: dict[str, Any]) -> None: ...

    async def format(
        self,
        arguments: dict[str, Any] | None = None,
    ) -> Sequence[PromptMessage]: ...
