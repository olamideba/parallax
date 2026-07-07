"""Opt-in pytest entry point for the efficiency benchmark.

Skipped by default (needs live Postgres + DashScope keys). Run explicitly:

    uv run pytest -m benchmark

Asserts the core Track 3 claim: the society is at least as accurate as the
single-agent baseline and catches at least as many fabricated/inflated-claim
traps. It does NOT assert a token/latency/cost win — the society is expected to
be pricier; buying accuracy with that spend is the point.
"""

from __future__ import annotations

import pytest

from tests.benchmark.run_benchmark import run


@pytest.mark.benchmark
async def test_society_beats_single_agent() -> None:
    result = await run()

    b, soc = result["baseline"], result["society"]
    assert result["n"] > 0, "no cases ran"
    assert soc["accuracy"] >= b["accuracy"], (
        f"society accuracy {soc['accuracy']} < baseline {b['accuracy']}"
    )
    assert soc["false_accepts"] <= b["false_accepts"], (
        f"society let through more traps ({soc['false_accepts']}) than baseline "
        f"({b['false_accepts']})"
    )
