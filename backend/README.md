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

## Benchmark: single-agent vs. agent society

`tests/benchmark/` measures the debate society against a strong single-agent
control (same RAG tool, same corpus, chain-of-thought reasoning) on 19
hand-labeled outreach cases — the Track 3 "measurable efficiency gain" deliverable.
The current trusted result lives in `tests/benchmark/out/report.md` /
`results.json` (society 90% accuracy vs. baseline 84%, at ~5.9x the tokens).

To re-run it yourself:

```bash
# One-time setup: local Postgres+pgvector needs the auth.users shim
# (professors.id has an FK to Supabase's auth.users, which doesn't exist on a
# plain pgvector image) — run once against your local DB:
docker exec <your-pgvector-container> psql -U <user> -d <db> -c \
  "CREATE SCHEMA IF NOT EXISTS auth; CREATE TABLE IF NOT EXISTS auth.users (id uuid PRIMARY KEY); \
   DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users; \
   INSERT INTO auth.users (id) VALUES ('11111111-1111-1111-1111-111111111111'), \
     ('22222222-2222-2222-2222-222222222222') ON CONFLICT DO NOTHING;"
DATABASE_URL="postgresql+asyncpg://<user>:<pass>@localhost:<port>/<db>" uv run alembic upgrade head

# Run the full 19-case benchmark (writes tests/benchmark/out/report.md + results.json)
./tests/benchmark/run_fair_comparison.sh

# Restrict to specific cases, or write to different output files (won't overwrite report.md)
./tests/benchmark/run_fair_comparison.sh --cases mata-strong-1 okoye-cap-1
./tests/benchmark/run_fair_comparison.sh --label my-run   # -> report_my-run.md

# Use a different model (must have quota + support structured output & tool calling)
MODEL=qwen3.6-flash ./tests/benchmark/run_fair_comparison.sh --label qwen36-flash
```

This is a real, live-token run against DashScope — expect ~600k tokens and
~20 minutes for the full 19 cases at the default config. See
`tests/benchmark/deep_dive_one_case.py` to dump a single case's full baseline
transcript + society debate trace + every rendered system prompt side by side,
for debugging why one path reached a given verdict.
