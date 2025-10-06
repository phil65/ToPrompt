from __future__ import annotations

from typing import Any


def format_dataclass_like(obj: Any) -> str:
    """Format object instance showing structure and current values."""
    from fieldz import fields

    try:
        obj_fields = fields(obj)
    except TypeError:
        return f"Unable to inspect fields of {type(obj)}"

    lines = [f"{type(obj).__name__}:\n{type(obj).__doc__}\n"]

    for field in obj_fields:
        if field.name.startswith("_"):
            continue
        value = getattr(obj, field.name)
        if field.description:
            lines.append(f"- {field.name} = {value!r} ({field.description})")
        else:
            type_name = field.type if field.type else "any"
            lines.append(f"- {field.name} = {value!r} ({type_name})")

    return "\n".join(lines)
