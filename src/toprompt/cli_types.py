from __future__ import annotations

import importlib.util
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable


if TYPE_CHECKING:
    from clinspector.models.commandinfo import CommandInfo


@runtime_checkable
class ClickCommandLike(Protocol):
    """Protocol for Click-like command objects."""

    name: str  # Click commands always have a name
    commands: dict[str, Any]  # Groups have subcommands
    params: list[Any]  # Click commands have params
    help: str | None  # Click commands can have help text


@runtime_checkable
class TyperCommandLike(Protocol):
    """Protocol for Typer-like command objects."""

    info: Any  # Typer instances have an info attribute
    registered_callback: Any  # And a registered_callback
    registered_commands: dict[str, Any]  # Commands are stored here


def is_click_command(obj: Any) -> bool:
    """Check if object looks like a Click command/group.

    Tries to detect Click commands by their distinctive attributes,
    without requiring Click to be installed.
    """
    return isinstance(obj, ClickCommandLike) and obj.__class__.__module__.startswith(
        "click"
    )


def is_typer_command(obj: Any) -> bool:
    """Check if object looks like a Typer app.

    Tries to detect Typer apps by their distinctive attributes,
    without requiring Typer to be installed.
    """
    return isinstance(obj, TyperCommandLike) and obj.__class__.__module__.startswith(
        "typer"
    )


def is_cli_object(obj: Any) -> bool:
    """Check if object is a supported CLI framework object.

    Safely checks for installed CLI frameworks before doing type checks.
    Prevents import errors if a framework is not installed.

    Args:
        obj: Object to check
    """
    # ArgumentParser is from stdlib, so we can always check it
    if importlib.util.find_spec("argparse"):
        import argparse

        if isinstance(obj, argparse.ArgumentParser):
            return True

    # Check Click
    if importlib.util.find_spec("click"):
        import click

        if isinstance(obj, click.Group):
            return True

    # Check Typer
    if importlib.util.find_spec("typer"):
        import typer

        if isinstance(obj, typer.Typer):
            return True

    # Check Cleo
    if importlib.util.find_spec("cleo"):
        from cleo.application import Application  # type: ignore

        if isinstance(obj, Application):
            return True

    # Check Cappa
    if importlib.util.find_spec("cappa"):
        from cappa import Command as CappaCommand  # type: ignore

        if isinstance(obj, CappaCommand):
            return True

    return False


def format_cli_command(
    info: CommandInfo,
    *,
    indent_level: int = 0,
) -> str:
    """Format a CommandInfo object into a prompt-friendly string recursively.

    Args:
        info: The CommandInfo object to format
        indent_level: Current indentation level for nested commands
    """
    indent = "  " * indent_level
    lines = [f"{indent}Command: {info.name}"]

    if info.description:
        lines.extend(["", f"{indent}Description: {info.description}"])

    if info.usage:
        lines.extend(["", f"{indent}Usage: {info.usage}"])

    if info.params:
        lines.extend(["", f"{indent}Parameters:"])
        for param in info.params:
            # Format parameter line
            parts = []

            # Add options/name
            if param.opts:
                parts.append(f"{', '.join(param.opts)}")
            else:
                parts.append(param.name)

            # Add type info
            if param.type:
                parts.append(f"({param.type})")

            # Add help text
            if param.help:
                parts.append(f"- {param.help}")

            # Add constraints
            constraints = []
            if param.required:
                constraints.append("required")
            if param.multiple:
                constraints.append("multiple values allowed")
            if param.is_flag:
                constraints.append("flag")
            if param.default is not None:
                constraints.append(f"default: {param.default}")

            if constraints:
                parts.append(f"[{', '.join(constraints)}]")

            lines.append(f"{indent}  {' '.join(parts)}")

    if info.subcommands:
        lines.extend(["", f"{indent}Subcommands:"])
        for subcmd in info.subcommands.values():
            # Recursively format each subcommand with increased indentation
            subcommand_text = format_cli_command(
                subcmd,
                indent_level=indent_level + 1,
            )
            lines.extend(["", subcommand_text])

    return "\n".join(lines)
