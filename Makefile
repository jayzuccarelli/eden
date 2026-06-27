# Canonical verify loop — `make check` is the self-grading gate for this repo.
.PHONY: check
check:
	uv run ruff check .
	uv run pytest -q
