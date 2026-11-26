# ToPrompt

[![PyPI License](https://img.shields.io/pypi/l/ToPrompt.svg)](https://pypi.org/project/ToPrompt/)
[![Package status](https://img.shields.io/pypi/status/ToPrompt.svg)](https://pypi.org/project/ToPrompt/)
[![Monthly downloads](https://img.shields.io/pypi/dm/ToPrompt.svg)](https://pypi.org/project/ToPrompt/)
[![Distribution format](https://img.shields.io/pypi/format/ToPrompt.svg)](https://pypi.org/project/ToPrompt/)
[![Wheel availability](https://img.shields.io/pypi/wheel/ToPrompt.svg)](https://pypi.org/project/ToPrompt/)
[![Python version](https://img.shields.io/pypi/pyversions/ToPrompt.svg)](https://pypi.org/project/ToPrompt/)
[![Implementation](https://img.shields.io/pypi/implementation/ToPrompt.svg)](https://pypi.org/project/ToPrompt/)
[![Releases](https://img.shields.io/github/downloads/phil65/ToPrompt/total.svg)](https://github.com/phil65/ToPrompt/releases)
[![Github Contributors](https://img.shields.io/github/contributors/phil65/ToPrompt)](https://github.com/phil65/ToPrompt/graphs/contributors)
[![Github Forks](https://img.shields.io/github/forks/phil65/ToPrompt)](https://github.com/phil65/ToPrompt/forks)
[![Github Issues](https://img.shields.io/github/issues/phil65/ToPrompt)](https://github.com/phil65/ToPrompt/issues)
[![Github Issues](https://img.shields.io/github/issues-pr/phil65/ToPrompt)](https://github.com/phil65/ToPrompt/pulls)
[![Github Watchers](https://img.shields.io/github/watchers/phil65/ToPrompt)](https://github.com/phil65/ToPrompt/watchers)
[![Github Stars](https://img.shields.io/github/stars/phil65/ToPrompt)](https://github.com/phil65/ToPrompt/stars)
[![Github Repository size](https://img.shields.io/github/repo-size/phil65/ToPrompt)](https://github.com/phil65/ToPrompt)
[![Github last commit](https://img.shields.io/github/last-commit/phil65/ToPrompt)](https://github.com/phil65/ToPrompt/commits)
[![Github release date](https://img.shields.io/github/release-date/phil65/ToPrompt)](https://github.com/phil65/ToPrompt/releases)
[![Github language count](https://img.shields.io/github/languages/count/phil65/ToPrompt)](https://github.com/phil65/ToPrompt)
[![Github commits this month](https://img.shields.io/github/commit-activity/m/phil65/ToPrompt)](https://github.com/phil65/ToPrompt)
[![Package status](https://codecov.io/gh/phil65/ToPrompt/branch/main/graph/badge.svg)](https://codecov.io/gh/phil65/ToPrompt/)
[![PyUp](https://pyup.io/repos/github/phil65/ToPrompt/shield.svg)](https://pyup.io/repos/github/phil65/ToPrompt/)

[Read the documentation!](https://phil65.github.io/ToPrompt/)

Convert Python objects into LLM-friendly text. `toprompt` provides one async function,
`to_prompt()`, that turns dataclasses, pydantic models, database schemas, CLI apps,
FastAPI apps and more into readable descriptions you can drop into a prompt.

## Installation

```bash
pip install toprompt
```

## Quickstart

```python
import asyncio
from dataclasses import dataclass

from toprompt import Template, to_prompt


@dataclass
class User:
    """A registered user."""

    name: str
    age: int


class Weather:
    def __prompt__(self) -> str:
        return "Sunny, 23 degrees"


async def main() -> None:
    print(await to_prompt(User("Alice", 30)))
    # User:
    # A registered user.
    #
    # - name = 'Alice' (<class 'str'>)
    # - age = 30 (<class 'int'>)

    print(await to_prompt({"user": User("Bob", 25), "weather": Weather()}))

    # Jinja templating (via MiniJinja) is opt-in
    template = Template("Hello {{ agent.name }}!")
    print(await to_prompt(template, template_mode="explicit", name="Bot"))  # Hello Bot!


asyncio.run(main())
```

## Supported objects

- **Strings** (returned as-is) and `Template` strings rendered with MiniJinja
  (`template_mode="explicit"`, or `"all"` to template every string)
- **Custom objects** implementing `__prompt__()` or a `__prompt_type__()` classmethod
  (sync or async), see the `PromptConvertible` / `PromptTypeConvertible` protocols
- **Structured objects** via [fieldz](https://github.com/pyapp-kit/fieldz): dataclasses,
  pydantic models, attrs classes, msgspec structs, ...
- **SQLModel** table classes and instances (table schema plus current values)
- **SQLite** connections (`sqlite3.Connection`): tables, columns, keys and indexes
- **CLI apps**: `argparse.ArgumentParser`, click commands/groups, typer apps, cleo and cappa
  (via [clinspector](https://github.com/phil65/clinspector))
- **FastAPI** apps: endpoints, parameters, request and response schemas
- **llmling** `BasePrompt` objects
- `datetime` (ISO format) and compiled regex patterns
- **Containers** (`dict`, `list`, `tuple`), converted recursively
- **Callables and coroutines**: called/awaited, and the result is converted

Framework integrations are optional: `toprompt` only uses them if they are installed.
