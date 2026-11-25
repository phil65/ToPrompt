# AGENTS.md

## Overview

`toprompt` converts Python objects into LLM-friendly text. The single entry point is the
async function `to_prompt(obj)`, which dispatches on the object's type (strings, templates,
objects with `__prompt__`/`__prompt_type__`, dataclasses / pydantic / attrs-like models,
SQLModel tables, SQLite databases, CLI apps, FastAPI apps, regex patterns, containers,
callables, coroutines) and returns a string.

## Architecture

All code lives in `src/toprompt/`:

- `__init__.py`: public API re-exports (`to_prompt`, `render_prompt`, `Template`,
  `PromptConvertible`, `PromptTypeConvertible`, `AnyPromptType`).
- `to_prompt.py`: the dispatcher. One big `match` statement in `to_prompt()`; the order of the
  `case` branches matters (e.g. `__prompt__` wins over field formatting, `str` before
  containers). Also holds `render_prompt()` (Jinja2 templating, used for `Template` strings when
  `template_mode` is `"explicit"` or `"all"`), the protocols, and detection helpers
  (`is_sqlmodel_table`, `is_base_prompt`, `can_format_fields`).
- `dataclass_types.py`: `format_dataclass_like()`, generic formatter via `fieldz` (dataclasses,
  pydantic, attrs, msgspec, ...).
- `sqlmodel_types.py`: `generate_schema_description()` for SQLModel table classes.
- `sqlite_types.py`: `is_sqlite_db()` / `get_sqlite_schema()` for `sqlite3.Connection` and DB paths.
- `cli_types.py`: detection of argparse/click/typer/cleo/cappa objects (`is_cli_object`) and
  `format_cli_command()` for `clinspector` `CommandInfo` trees.
- `fastapi_types.py`: `FastApiAppLike` protocol and `format_fastapi_app()` (reads `app.openapi()`).
- `llmling_types.py`: protocol for llmling `BasePrompt` objects.
- `log.py`: `get_logger()` helper.

Control flow: `to_prompt()` recurses for dicts/lists/tuples (via `asyncio.gather`), awaits
coroutines, calls zero-arg callables and converts their result again.

## Where to look

| Task | Location |
|------|----------|
| Add support for a new object type | new `src/toprompt/<x>_types.py` + a `case` in `to_prompt.py` |
| Change templating | `render_prompt()` in `src/toprompt/to_prompt.py` |
| CLI formatting | `src/toprompt/cli_types.py` |
| Database schemas | `src/toprompt/sqlite_types.py`, `src/toprompt/sqlmodel_types.py` |
| Tests | `tests/test_toprompt.py` |
| CI | `.github/workflows/build.yml`, `.github/workflows/documentation.yml` |
| Dev tasks | `duties.py` |

## Commands

```bash
uv sync --all-extras                 # setup (default groups: dev, lint, docs)
uv run pytest                        # tests
uvx ruff check . && uvx ruff format --check .
uv run ty check                      # type check (src only, warnings fail too)
uv run deptry src                    # dependency check
uv run mknodes build                 # docs build (output in site/)
uv build                             # package
uv run duty lint | lint_check | test | build | serve | update   # duties.py shortcuts
```

Pre-commit hooks (`.pre-commit-config.yaml`) run ruff, tombi, ty and pytest.

## Conventions

- Python >= 3.13, `from __future__ import annotations` everywhere, Google-style docstrings.
- Ruff with a broad rule set (line length 100, preview formatting); `datetime` must be imported
  as `dt` in new code (ICN001).
- Type checking with ty, not mypy. Use `cast(...)` or targeted `# ty: ignore[rule]`, no
  mypy-style `# type: ignore[code]`.
- Tests are plain `async def test_*` functions; `asyncio_mode = "auto"` (pytest-asyncio), so no
  marker is needed. pytest config lives in the native `[tool.pytest]` table (pytest 9).
- Integrations detect frameworks by duck typing or `importlib.util.find_spec` and import them
  lazily inside the branch. Never import optional frameworks at module level.

## Pitfalls

- Copier-managed project (`.copier-answers.yml`, template `copier-phil65`). Workflows,
  `duties.py`, `.pre-commit-config.yaml`, `mkdocs.yml` and most of `pyproject.toml` come from
  the template; add dependencies only below the `# Only add below (Copier)` markers.
- Optional integrations (click, typer, cleo, cappa, llmling, fastapi, sqlmodel) are not runtime
  dependencies. Directly imported ones are listed in `[tool.deptry.per_rule_ignores]`;
  sqlmodel is in the dev group (tests, type checking); `llmling` is in
  `[tool.ty.analysis] allowed-unresolved-imports`. `duty` is not declared and comes in
  transitively via the docs group.
- `to_prompt()` is async; call it with `await` or `asyncio.run()`.
- `template_mode="all"` renders every string as a Jinja2 template; only use it with trusted input.
- The docs site is the mknodes default site (README + generated API pages); `docs/` is
  empty on purpose.
