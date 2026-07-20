# CLAUDE.md

## Tooling

Python is managed with **uv** and linted/formatted with **ruff**: use them, not `pip`/`black`/`flake8`.

- `uv sync` to set up; `uv run <cmd>` to run anything (`uv run pytest`, `uv run python -m eden`).
- `uv add <pkg>` / `uv add --dev <pkg>` to change deps; commit the updated `uv.lock`.
- Before committing code: `uv run ruff check --fix` and `uv run ruff format`. Keep the tree lint-clean.
