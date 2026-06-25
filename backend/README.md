# Parallax — backend

## Setup

```bash
cd backend
cp .env.example .env   # fill in values
uv sync
```

## Run

```bash
# API server
uv run uvicorn src.entrypoints.api.main:app --reload

# Worker (separate terminal)
uv run celery -A src.entrypoints.workers.celery_app worker --loglevel=info

# Or via main.py
uv run python main.py
```

## Database migrations

```bash
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
```

## Tests

```bash
uv run pytest
uv run ruff check src
```
