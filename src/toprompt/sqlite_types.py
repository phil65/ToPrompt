from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING, Any, Protocol, TypedDict, runtime_checkable

import upath


if TYPE_CHECKING:
    import os


@runtime_checkable
class InMemoryDatabaseLike(Protocol):
    """Protocol for in-memory database-like objects."""

    @property
    def in_memory(self) -> bool: ...


@runtime_checkable
class FileDatabaseLike(Protocol):
    """Protocol for file-based database-like objects."""

    @property
    def _filename(self) -> str | None: ...


class ColumnInfo(TypedDict):
    """Information about a SQLite column."""

    name: str
    type: str
    notnull: bool
    default: str | None
    pk: bool


class ForeignKeyInfo(TypedDict):
    """Information about a SQLite foreign key."""

    from_table: str
    from_col: str
    to_table: str
    to_col: str


class IndexInfo(TypedDict):
    """Information about a SQLite index."""

    name: str
    table: str
    unique: bool
    columns: list[str]


def is_sqlite_db(obj: Any) -> bool:
    """Check if object is a SQLite database."""
    return isinstance(obj, sqlite3.Connection)


def get_db_path(conn: sqlite3.Connection) -> str:
    """Get the path for a SQLite database connection."""
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA database_list")
        # This returns rows with (seq, name, file) for each database
        for _, name, file_path in cursor.fetchall():
            if name == "main":  # main database
                return file_path or ":memory:"
    except sqlite3.Error:
        pass
    return ":memory:"  # fallback to memory if we can't determine


def get_sqlite_schema(db: str | os.PathLike[str] | sqlite3.Connection) -> str:
    """Generate human-readable documentation from SQLite database.

    Args:
        db: Path to SQLite database file or Connection object
    """
    if isinstance(db, sqlite3.Connection):
        conn = db
        should_close = False
    else:
        path = upath.UPath(db)
        if not path.exists():
            msg = f"Database file not found: {path}"
            raise FileNotFoundError(msg)
        conn = sqlite3.connect(path)
        should_close = True

    try:
        cursor = conn.cursor()
        # Get all tables
        tables = get_tables(cursor)
        if not tables:
            return "Database contains no tables."

        lines = ["SQLite Database Schema:"]

        # Process each table
        for table in tables:
            lines.extend(get_table_info(cursor, table))
            lines.append("")  # Empty line between tables

        return "\n".join(lines)

    finally:
        if should_close:
            conn.close()


def get_tables(cursor: sqlite3.Cursor) -> list[str]:
    """Get all table names from database."""
    cursor.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type='table'
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    )
    return [row[0] for row in cursor.fetchall()]


def get_table_info(cursor: sqlite3.Cursor, table: str) -> list[str]:
    """Get detailed information about a specific table."""
    # Get column information
    cursor.execute(f"PRAGMA table_info({table})")
    columns: list[ColumnInfo] = [
        {
            "name": row[1],
            "type": row[2],
            "notnull": bool(row[3]),
            "default": row[4],
            "pk": bool(row[5]),
        }
        for row in cursor.fetchall()
    ]

    # Get foreign keys
    cursor.execute(f"PRAGMA foreign_key_list({table})")
    foreign_keys: list[ForeignKeyInfo] = [
        {
            "from_table": table,
            "from_col": row[3],
            "to_table": row[2],
            "to_col": row[4],
        }
        for row in cursor.fetchall()
    ]

    # Get indices
    cursor.execute(
        """
        SELECT name, sql FROM sqlite_master
        WHERE type='index'
        AND tbl_name=?
        AND name NOT LIKE 'sqlite_%'
        """,
        (table,),
    )
    indices = get_index_info(cursor, table)

    # Format table documentation
    lines = [f"\nTable: {table}"]

    # Columns
    lines.append("\nColumns:")
    for col in columns:
        parts = [f"- {col['name']}: {col['type']}"]
        properties = []

        if col["pk"]:
            properties.append("primary key")
        if col["notnull"]:
            properties.append("not null")
        if col["default"] is not None:
            properties.append(f"default: {col['default']}")

        if properties:
            parts.append(f"({', '.join(properties)})")
        lines.append(" ".join(parts))

    # Foreign Keys
    if foreign_keys:
        lines.append("\nForeign Keys:")
        lines.extend(
            f"- {fk['from_col']} -> {fk['to_table']}.{fk['to_col']}"
            for fk in foreign_keys
        )

    # Indices
    if indices:
        lines.append("\nIndices:")
        for idx in indices:
            unique = "UNIQUE " if idx["unique"] else ""
            cols = ", ".join(idx["columns"])
            lines.append(f"- {idx['name']}: {unique}({cols})")

    return lines


def get_index_info(cursor: sqlite3.Cursor, table: str) -> list[IndexInfo]:
    """Get information about indices on a table."""
    cursor.execute(
        """
        SELECT name, sql FROM sqlite_master
        WHERE type='index'
        AND tbl_name=?
        AND name NOT LIKE 'sqlite_%'
        """,
        (table,),
    )
    indices: list[IndexInfo] = []

    for name, sql in cursor.fetchall():
        if not sql:
            continue

        # Parse SQL to extract column names and uniqueness
        sql = sql.upper()
        unique = "UNIQUE " in sql
        # Extract column list from parentheses
        cols_start = sql.find("(")
        cols_end = sql.rfind(")")
        if cols_start == -1 or cols_end == -1:
            continue

        cols = sql[cols_start + 1 : cols_end]
        columns = [c.strip() for c in cols.split(",")]

        indices.append({
            "name": name,
            "table": table,
            "unique": unique,
            "columns": columns,
        })

    return indices
