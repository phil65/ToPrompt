import annotationlib
from typing import Any, ForwardRef


def _type_name(tp: Any) -> str:
    """Readable name of a field type (a string, a ForwardRef or a type)."""
    if not tp:
        return "any"
    if isinstance(tp, str):
        return tp
    if isinstance(tp, ForwardRef):
        return tp.__forward_arg__
    return annotationlib.type_repr(tp)


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
            lines.append(f"- {field.name} = {value!r} ({_type_name(field.type)})")

    return "\n".join(lines)
