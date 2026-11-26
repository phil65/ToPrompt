from __future__ import annotations

import argparse
import asyncio
from collections.abc import Awaitable, Callable, Coroutine
from datetime import datetime
import functools
import re
import sys
from typing import TYPE_CHECKING, Any, Literal, Protocol, cast

from pydantic import BaseModel

from toprompt.cli_types import (
    ClickCommandLike,
    TyperCommandLike,
    format_cli_command,
    is_cli_object,
)
from toprompt.dataclass_types import format_dataclass_like
from toprompt.fastapi_types import FastApiAppLike, format_fastapi_app
from toprompt.llmling_types import BasePromptProtocol
from toprompt.sqlite_types import (
    FileDatabaseLike,
    InMemoryDatabaseLike,
    get_sqlite_schema,
    is_sqlite_db,
)


if TYPE_CHECKING:
    from sqlmodel import SQLModel


class PromptConvertible(Protocol):
    """Protocol for instances that can be converted to prompts."""

    def __prompt__(self) -> str | Awaitable[str]: ...


class PromptTypeConvertible(Protocol):
    """Protocol for types that can be converted to prompts."""

    @classmethod
    def __prompt_type__(cls) -> str | Awaitable[str]: ...


class FieldFormattable(Protocol):
    """Protocol for types that can be formatted through their fields."""

    __annotations__: dict[str, Any]


type AnyPromptType = (
    str
    | PromptConvertible
    | PromptTypeConvertible
    | FieldFormattable
    | BaseModel
    | InMemoryDatabaseLike
    | ClickCommandLike
    | TyperCommandLike
    | BasePromptProtocol
    | argparse.ArgumentParser
    | FileDatabaseLike
    | datetime
    | FastApiAppLike
    | re.Pattern
    | dict[str, Any]
    | list[Any]
    | tuple[Any, ...]
    | Callable[..., str]
    | Coroutine[Any, Any, str]
)


class Template(str):  # noqa: SLOT000
    """Marker class for strings that should be templated."""


async def to_prompt(  # noqa: PLR0911
    obj: AnyPromptType,
    *,
    template_mode: Literal["off", "explicit", "all"] = "off",
    **kwargs: Any,
) -> str:
    """Convert any supported type to a prompt string.

    Args:
        obj: Object to convert
        template_mode: How to handle templating:
            - "off": No templating (default)
            - "explicit": Only Template instances
            - "all": Template all strings (dangerous!)
        **kwargs: Template variables (available as ``agent.<key>``) if templating
            is enabled

    Returns:
        A text representation of the object
    """
    match obj:
        case Template() if template_mode != "off":
            return render_prompt(obj, kwargs)

        case str() if template_mode == "all":
            return render_prompt(obj, kwargs)

        case str():
            return obj

        case type() if hasattr(obj, "__prompt_type__"):
            result = cast("type[PromptTypeConvertible]", obj).__prompt_type__()
            if isinstance(result, Awaitable):
                return await result
            return result

        # Not for classes: their __prompt__ is an unbound instance method.
        case _ if hasattr(obj, "__prompt__") and not isinstance(obj, type):
            result = cast("PromptConvertible", obj).__prompt__()
            if isinstance(result, Awaitable):
                return await result
            return result

        case datetime():
            return obj.isoformat()

        case FastApiAppLike():
            return format_fastapi_app(obj)

        case re.Pattern():
            flags = []
            if obj.flags & re.IGNORECASE:
                flags.append("ignorecase")
            if obj.flags & re.MULTILINE:
                flags.append("multiline")
            if obj.flags & re.DOTALL:
                flags.append("dotall")
            if obj.flags & re.VERBOSE:
                flags.append("verbose")
            flags_str = f" ({', '.join(flags)})" if flags else ""
            return f"Pattern: {obj.pattern!r}{flags_str}"

        case _ if is_base_prompt(obj):
            from llmling import BasePrompt

            assert isinstance(obj, BasePrompt)
            messages = await obj.format(kwargs)
            return "\n".join(msg.get_text_content() for msg in messages)

        case type() if is_sqlmodel_table(obj):
            from toprompt.sqlmodel_types import generate_schema_description

            return generate_schema_description(cast("type[SQLModel]", obj))

        case _ if is_sqlmodel_table(type(obj)):  # SQLModel instance
            from toprompt.sqlmodel_types import generate_schema_description

            # Get class documentation first
            schema_doc = generate_schema_description(cast("type[SQLModel]", type(obj)))
            # Add current values
            values = "\nCurrent Values:\n"
            for field_name, value in obj.__dict__.items():
                if not field_name.startswith("_"):
                    values += f"- {field_name}: {value!r}\n"
            return schema_doc + values

        case _ if is_cli_object(obj):
            from clinspector import get_cmd_info

            cmd_info = get_cmd_info(obj)
            if cmd_info is None:
                msg = f"Could not get CLI info for {type(obj)}"
                raise ValueError(msg)
            return format_cli_command(cmd_info)

        case _ if can_format_fields(obj):
            return format_dataclass_like(obj)
        case dict():
            results = await asyncio.gather(
                *(to_prompt(v, template_mode=template_mode, **kwargs) for v in obj.values())
            )
            return "\n".join(f"{k}: {r}" for (k, _), r in zip(obj.items(), results))

        case _ if is_sqlite_db(obj):
            # Pass the connection directly for in-memory databases
            return get_sqlite_schema(obj)  # type: ignore

        case list() | tuple():
            items = await asyncio.gather(
                *(to_prompt(item, template_mode=template_mode, **kwargs) for item in obj)
            )
            return "\n".join(items)

        case Coroutine():
            result = await obj
            return await to_prompt(result, template_mode=template_mode, **kwargs)

        # Calling a class would instantiate it (side effects, required arguments).
        case _ if callable(obj) and not isinstance(obj, type):
            result = obj()
            return await to_prompt(result, template_mode=template_mode, **kwargs)

        case _:
            return str(obj)


def is_sqlmodel_table(obj: Any) -> bool:
    """Check whether obj is a SQLModel table class (``table=True``)."""
    if not isinstance(obj, type) or not hasattr(obj, "__table__"):
        return False
    return any(
        base.__name__ == "SQLModel" and base.__module__.startswith("sqlmodel")
        for base in obj.__mro__
    )


def is_base_prompt(obj: Any) -> bool:
    # An instance can only exist once its module is imported: no find_spec / import.
    if (llmling := sys.modules.get("llmling")) is None:
        return False
    return isinstance(obj, llmling.BasePrompt)


@functools.cache
def _jinja_env() -> Any:
    from jinja2 import Environment

    # Prompts are plain text for an LLM, not HTML: no autoescaping.
    return Environment(autoescape=False, keep_trailing_newline=True)


def render_prompt(
    template: str,
    agent_context: dict[str, Any],
) -> str:
    """Render a Jinja2 prompt template.

    The context is exposed to the template as ``agent``, e.g.
    ``render_prompt("Hi {{ agent.name }}", {"name": "Bot"})`` returns ``"Hi Bot"``.

    Args:
        template: Jinja2 template string
        agent_context: Variables available as ``agent.<key>`` in the template

    Returns:
        The rendered string
    """
    tpl = _jinja_env().from_string(template)
    return tpl.render(agent=agent_context)


def can_format_fields(obj: Any) -> bool:
    """Check if object can be inspected by fieldz."""
    from fieldz import get_adapter

    try:
        get_adapter(obj)
    except TypeError:
        return False
    else:
        return True
