from __future__ import annotations

import time
from typing import Any
from uuid import UUID

from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult
from loguru import logger

# Process-wide running total, logged per-debate by the engine. A debate runs
# start-to-finish inside one asyncio.run in one worker process, so a simple
# module-level accumulator keyed by nothing is fine here — but we expose a
# reset/snapshot pair so the engine can bracket one debate's cost cleanly.
_totals: dict[str, int] = {"calls": 0, "input": 0, "output": 0}


def reset_token_totals() -> None:
    _totals.update(calls=0, input=0, output=0)


def token_totals() -> dict[str, int]:
    return dict(_totals)


class TokenUsageCallback(AsyncCallbackHandler):
    """Logs latency + token usage for every LLM call, tagged with the agent
    role, and rolls the counts into a per-debate running total.

    Attached at model construction (chat_model.get_chat_model) so it covers
    every .ainvoke in the engine — debater turns, moderator routing, the
    arbitrator ruling — with no per-call-site wiring.
    """

    def __init__(self, role: str, model: str) -> None:
        self._role = role
        self._model = model
        self._starts: dict[UUID, float] = {}

    async def on_llm_start(
        self, serialized: dict[str, Any], prompts: list[str], *, run_id: UUID, **_: Any
    ) -> None:
        self._starts[run_id] = time.perf_counter()

    async def on_llm_end(self, response: LLMResult, *, run_id: UUID, **_: Any) -> None:
        started = self._starts.pop(run_id, None)
        elapsed_ms = int((time.perf_counter() - started) * 1000) if started else 0

        usage = _extract_usage(response)
        in_tok, out_tok = usage
        _totals["calls"] += 1
        _totals["input"] += in_tok
        _totals["output"] += out_tok

        logger.debug(
            "  ↳ {} · {} · {}ms · {}+{} tok",
            self._role,
            self._model,
            elapsed_ms,
            in_tok,
            out_tok,
        )

    async def on_llm_error(self, error: BaseException, *, run_id: UUID, **_: Any) -> None:
        self._starts.pop(run_id, None)
        logger.warning("  ↳ {} · {} · LLM error: {}", self._role, self._model, error)


def _extract_usage(response: LLMResult) -> tuple[int, int]:
    """Pull (input, output) token counts from an LLMResult. langchain surfaces
    usage on message.usage_metadata; some providers only fill llm_output."""
    for generations in response.generations:
        for gen in generations:
            message = getattr(gen, "message", None)
            meta = getattr(message, "usage_metadata", None)
            if meta:
                return int(meta.get("input_tokens", 0)), int(meta.get("output_tokens", 0))
    llm_output = response.llm_output or {}
    token_usage = llm_output.get("token_usage") or llm_output.get("usage") or {}
    return (
        int(token_usage.get("prompt_tokens", 0)),
        int(token_usage.get("completion_tokens", 0)),
    )
