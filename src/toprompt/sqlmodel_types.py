from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING, TypeVar


if TYPE_CHECKING:
    from sqlmodel import SQLModel


T = TypeVar("T")


def generate_schema_description(model: type[SQLModel]) -> str:
    """Generate human-readable schema documentation from SQLModel."""
    table = model.__table__  # type: ignore
    fields: list[str] = []

    # Get primary keys
    pk_cols = [c.name for c in table.primary_key.columns]

    # Get field descriptions from model
    docs = {n: f.description for n, f in model.model_fields.items() if f.description}
    # Process each column
    for column in table.columns:
        parts = []
        # Name and type
        parts.append(f"- {column.name}: {column.type}")

        # Add docstring if available
        if doc := docs.get(column.name):
            parts.append(f"\n  Description: {doc}")

        # Add column properties
        properties = []
        if column.name in pk_cols:
            properties.append("primary key")
        if column.foreign_keys:
            fks = [f"references {fk.column.table.name}" for fk in column.foreign_keys]
            properties.append(f"foreign key ({', '.join(fks)})")
        if not column.nullable:
            properties.append("not null")
        if column.default:
            properties.append(f"default: {column.default.arg}")
        if column.server_default:
            properties.append("has server default")
        if properties:
            parts.append(f"  ({', '.join(properties)})")

        fields.append(" ".join(parts))

    # Build complete description
    return dedent(f"""
        Table: {table.name}
        Description: {model.__doc__ or "No description available"}

        Fields:
        {chr(10).join(fields)}
        """)
