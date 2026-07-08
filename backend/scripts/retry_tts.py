#!/usr/bin/env python
"""Retry TTS synthesis for a debate trace, out of band from the pipeline.

The normal path synthesizes audio automatically after run_debate. This script
re-runs just the synthesis step for an already-debated outreach — useful after
fixing a synthesis bug, changing voices, or a partial failure.

Usage (from backend/):
    uv run python scripts/retry_tts.py <outreach_id> [<outreach_id> ...]
    uv run python scripts/retry_tts.py <outreach_id> --no-force

By default force=True, so every turn is re-synthesized (overwriting existing
audio). Pass --no-force to only fill in turns that don't have audio yet.
"""

from __future__ import annotations

import asyncio
import sys
from uuid import UUID

from src.entrypoints.workers.intake_consumer import _synthesize_debate_audio


async def _main(outreach_ids: list[UUID], force: bool) -> int:
    total = 0
    for oid in outreach_ids:
        try:
            count = await _synthesize_debate_audio(oid, force=force)
            print(f"{oid}: synthesized {count} turns")
            total += count
        except Exception as exc:  # noqa: BLE001
            print(f"{oid}: FAILED - {type(exc).__name__}: {exc}", file=sys.stderr)
    return total


def main() -> None:
    args = [a for a in sys.argv[1:] if a not in ("--no-force", "--force")]
    force = "--no-force" not in sys.argv

    if not args:
        print(__doc__)
        sys.exit(1)

    try:
        outreach_ids = [UUID(a) for a in args]
    except ValueError as exc:
        print(f"Invalid outreach id: {exc}", file=sys.stderr)
        sys.exit(1)

    asyncio.run(_main(outreach_ids, force))


if __name__ == "__main__":
    main()
