# CLAUDE.md

## Issue tracking (Linear)

Work for this repo (the HA config garden / Gardener agent) is tracked in Linear — an internal tracker, project **ha-config**.

- **Keep Linear tidy as you work, without being asked.** When Jay asks you to fix/build something, first check it has an issue in the **ha-config** project (`list_issues`, team JAY, project `ha-config`) — if not, create one. When he says "remember to do X later," file it. Mark issues In Progress when you start; make sure they end up Done when finished.
- Found a bug, TODO, or follow-up? File it as a Linear issue in the **ha-config** project instead of leaving a stray code comment or a separate list.
- Linear generates a branch name per issue (`jayzuccarelli/jay-NN-...`); work on that branch.
- Put `Fixes JAY-NN` in the PR description or a commit message — merging then auto-closes the issue.
- Don't keep a parallel todo list; Linear is the source of truth.

## Tooling

Python is managed with **uv** and linted/formatted with **ruff** — use them, not `pip`/`black`/`flake8`.

- `uv sync` to set up; `uv run <cmd>` to run anything (`uv run pytest`, `uv run python -m eden`).
- `uv add <pkg>` / `uv add --dev <pkg>` to change deps; commit the updated `uv.lock`.
- Before committing code: `uv run ruff check --fix` and `uv run ruff format`. Keep the tree lint-clean.
