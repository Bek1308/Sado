# Sado server

FastAPI backend for speech, reasoning and memory. Layout and rules: [Engineering principles](../docs/ENGINEERING.md).

## Run

```bash
uv sync
uv run uvicorn sado.main:app --reload
```

Open http://localhost:8000/docs for the interactive API.

## Check

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
```
