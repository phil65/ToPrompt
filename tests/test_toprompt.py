from __future__ import annotations

import argparse
from dataclasses import dataclass
import datetime as dt
import re
import sqlite3

from pydantic import BaseModel
import pytest

from toprompt import to_prompt


@dataclass
class SimpleDataclass:
    """A simple dataclass for testing."""

    name: str
    value: int


class PydanticModel(BaseModel):
    """A simple pydantic model for testing."""

    name: str
    value: int


async def test_basic_types():
    """Test basic stdlib types."""
    # Simple types
    assert await to_prompt("test") == "test"
    assert await to_prompt(123) == "123"
    assert await to_prompt(True) == "True"

    # Collections
    assert await to_prompt(["a", "b"]) == "a\nb"
    assert await to_prompt({"a": 1, "b": 2}) == "a: 1\nb: 2"
    assert await to_prompt(("x", "y")) == "x\ny"

    # Datetime
    dt_obj = dt.datetime(2024, 1, 1, 12, 0)
    assert await to_prompt(dt_obj) == "2024-01-01T12:00:00"

    # Regex
    pattern = re.compile(r"\d+", re.IGNORECASE)
    result = await to_prompt(pattern)
    assert "Pattern" in result
    assert r"\d+" in result
    assert "ignorecase" in result


async def test_dataclass():
    """Test dataclass support."""
    obj = SimpleDataclass(name="test", value=42)
    result = await to_prompt(obj)
    assert "SimpleDataclass" in result
    assert "test" in result
    assert "42" in result


async def test_pydantic():
    """Test pydantic model support."""
    obj = PydanticModel(name="test", value=42)
    result = await to_prompt(obj)
    assert "test" in result
    assert "42" in result


async def test_argparse():
    """Test ArgumentParser support."""
    parser = argparse.ArgumentParser(description="Test parser")
    parser.add_argument("--flag", help="A flag")
    result = await to_prompt(parser)
    assert "Test parser" in result
    assert "--flag" in result


async def test_sqlite():
    """Test SQLite support."""
    # Create a temporary in-memory database
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")

    result = await to_prompt(conn)
    assert "SQLite Database Schema" in result
    assert "test" in result
    assert "id" in result
    assert "name" in result

    conn.close()


async def test_sqlmodel_table():
    from sqlmodel import Field, SQLModel

    class Hero(SQLModel, table=True):
        """A hero."""

        id: int | None = Field(default=None, primary_key=True)
        name: str = Field(description="Hero name")

    result = await to_prompt(Hero)
    assert result.startswith("Table: hero")
    assert "Description: Hero name" in result

    result = await to_prompt(Hero(name="x"))
    assert "Table: hero" in result
    assert "- name: 'x'" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


async def test_templates_are_not_html_escaped():
    from toprompt import Template

    text = 'a < b & "c" it\'s'
    result = await to_prompt(Template("{{ agent.q }}"), template_mode="explicit", q=text)
    assert result == text


async def test_template_mode_and_variables_survive_recursion():
    from toprompt import Template

    tpl = Template("x={{ agent.x }}")
    assert await to_prompt([tpl], template_mode="explicit", x=1) == "x=1"
    assert await to_prompt({"k": tpl}, template_mode="explicit", x=1) == "k: x=1"
    assert await to_prompt((tpl,), template_mode="explicit", x=2) == "x=2"

    async def coro() -> str:
        return tpl

    assert await to_prompt(coro(), template_mode="explicit", x=3) == "x=3"
    assert await to_prompt(lambda: tpl, template_mode="explicit", x=4) == "x=4"


async def test_classes_are_not_instantiated():
    created = []

    class SideEffect:
        def __init__(self) -> None:
            created.append(self)

    class WithPrompt:
        def __prompt__(self) -> str:
            return "instance prompt"

    assert await to_prompt(int) == str(int)
    assert await to_prompt(SideEffect) == str(SideEffect)
    assert created == []
    assert await to_prompt(WithPrompt) == str(WithPrompt)
    assert await to_prompt(WithPrompt()) == "instance prompt"


async def test_unrecognized_objects_do_not_probe_find_spec(monkeypatch):
    import importlib.util

    calls = []
    real = importlib.util.find_spec

    def spy(name: str, *args: object) -> object:
        calls.append(name)
        return real(name, *args)

    monkeypatch.setattr(importlib.util, "find_spec", spy)
    assert await to_prompt([object()] * 3)
    assert calls == []


async def test_cli_objects_still_detected():
    import click

    @click.group()
    def cli() -> None:
        """A CLI."""

    assert "cli" in (await to_prompt(cli)).lower()


async def test_sqlite_quoted_table_names_and_index_case():
    conn = sqlite3.connect(":memory:")
    conn.execute('CREATE TABLE "order items" (id INTEGER PRIMARY KEY, userName TEXT)')
    conn.execute(
        'CREATE TABLE "select" ("weird""col" TEXT, ref INTEGER REFERENCES "order items"(id))'
    )
    conn.execute('CREATE UNIQUE INDEX idx_user ON "order items"(userName)')
    conn.execute('CREATE INDEX "idx ""q""" ON "select"(ref, "weird""col")')
    result = await to_prompt(conn)
    assert "Table: order items" in result
    assert "- idx_user: UNIQUE (userName)" in result
    assert "Table: select" in result
    assert '- weird"col: TEXT' in result
    assert "- ref -> order items.id" in result
    assert '- idx "q": (ref, weird"col)' in result
    conn.close()


def test_sqlite_file_opened_read_only(tmp_path, monkeypatch):
    from toprompt.sqlite_types import get_sqlite_schema

    path = tmp_path / "my db#1?.sqlite"
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE t (id INTEGER)")
    conn.commit()
    conn.close()
    real_connect = sqlite3.connect
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def spy(*args: object, **kwargs: object) -> sqlite3.Connection:
        calls.append((args, kwargs))
        return real_connect(*args, **kwargs)  # type: ignore[call-overload]

    monkeypatch.setattr(sqlite3, "connect", spy)
    assert "Table: t" in get_sqlite_schema(path)
    [(args, kwargs)] = calls
    assert kwargs.get("uri") is True
    assert str(args[0]).endswith("?mode=ro")
