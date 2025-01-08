from __future__ import annotations

import argparse
from dataclasses import dataclass
import datetime
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


@pytest.mark.asyncio
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
    dt = datetime.datetime(2024, 1, 1, 12, 0)
    assert await to_prompt(dt) == "2024-01-01T12:00:00"

    # Regex
    pattern = re.compile(r"\d+", re.IGNORECASE)
    result = await to_prompt(pattern)
    assert "Pattern" in result
    assert r"\d+" in result
    assert "ignorecase" in result


@pytest.mark.asyncio
async def test_dataclass():
    """Test dataclass support."""
    obj = SimpleDataclass(name="test", value=42)
    result = await to_prompt(obj)
    assert "SimpleDataclass" in result
    assert "test" in result
    assert "42" in result


@pytest.mark.asyncio
async def test_pydantic():
    """Test pydantic model support."""
    obj = PydanticModel(name="test", value=42)
    result = await to_prompt(obj)
    assert "test" in result
    assert "42" in result


@pytest.mark.asyncio
async def test_argparse():
    """Test ArgumentParser support."""
    parser = argparse.ArgumentParser(description="Test parser")
    parser.add_argument("--flag", help="A flag")
    result = await to_prompt(parser)
    assert "Test parser" in result
    assert "--flag" in result


@pytest.mark.asyncio
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
