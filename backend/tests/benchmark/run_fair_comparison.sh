#!/usr/bin/env bash
# Re-runs the trusted single-agent-vs-society benchmark: society at its real
# production depth (round-cap 3) with a token ceiling equalized to the
# single-agent baseline (2000/call on both sides), so neither path is
# artificially throttled. This is the config behind tests/benchmark/out/report.md.
#
# Requires: local Postgres+pgvector reachable at DATABASE_URL below (override
# if needed) with the auth.users shim + migrations applied (see README.md in
# this directory), and a live DASHSCOPE_API_KEY in backend/.env.
#
# Usage (from backend/):
#   ./tests/benchmark/run_fair_comparison.sh
#   ./tests/benchmark/run_fair_comparison.sh --cases mata-strong-1 okoye-cap-1
#   MODEL=qwen3.6-flash ./tests/benchmark/run_fair_comparison.sh --label my-run

set -euo pipefail
cd "$(dirname "$0")/../.."

MODEL="${MODEL:-qwen3.5-plus-2026-02-15}"
DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://parallax:parallax@localhost:5434/parallax}"

QWEN_MODEL_GATEKEEPER="$MODEL" \
QWEN_MODEL_DEBATE="$MODEL" \
QWEN_MODEL_ARBITRATOR="$MODEL" \
DEBATE_ROUND_CAP=3 \
DEBATE_TURN_CAP_MULTIPLIER=2 \
DEBATE_MAX_TOOL_ROUNDS=3 \
DEBATE_MAX_CONTINUATIONS=2 \
DEBATE_ARBITER_ATTEMPTS=3 \
DEBATE_MAX_TURN_TOKENS=2000 \
DEBATE_MAX_ARBITER_TOKENS=2000 \
DATABASE_URL="$DATABASE_URL" \
uv run python -m tests.benchmark.run_benchmark "$@"
