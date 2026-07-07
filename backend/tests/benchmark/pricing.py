"""Per-model USD token pricing for the benchmark's cost column.

There is no pricing config in `src/` (cost never enters the product path), so the
benchmark ships its own table. Rates are the International (Singapore) endpoint —
the hackathon target host (dashscope-intl) — and were taken from published Qwen
pricing as of 2026-07. **These are not guessed:** a fabricated rate is exactly the
kind of unsupported number this benchmark exists to expose, so any model whose
rate could not be corroborated is left `None` and its cost reports as N/A rather
than inventing a figure. Re-verify against the live pricing page before quoting
dollar figures in the submission:
https://www.alibabacloud.com/help/en/model-studio/model-pricing

Units: USD per 1,000,000 tokens.
"""

from __future__ import annotations

# model_id -> (usd_per_million_input, usd_per_million_output) or None if unverified.
PRICING_USD_PER_M: dict[str, tuple[float, float] | None] = {
    # Corroborated across independent 2026 price trackers (Singapore endpoint).
    "qwen3.5-flash": (0.065, 0.260),
    # Dated snapshot of qwen3.5-flash — same tier, same published rate.
    "qwen3.5-flash-2026-02-23": (0.065, 0.260),
    "qwen3.6-flash": (0.19, 1.13),
    # qwen-turbo: input ~$0.033/M is reported, but the output rate could not be
    # corroborated and the model is deprecated in favor of qwen-flash. Left
    # unverified rather than guessed — it's only the cheap Gatekeeper/moderator
    # pass, a small share of debate tokens.
    "qwen-turbo": None,
}


class UnknownModelCost(Exception):
    """Raised only when strict costing is requested for an unpriced model."""


def cost_usd(model_id: str, input_tokens: int, output_tokens: int) -> float | None:
    """USD cost for a call, or None if the model has no verified rate.

    Callers treat None as "N/A" in the report — we never substitute a made-up
    rate to fill the column.
    """
    rate = PRICING_USD_PER_M.get(model_id)
    if rate is None:
        return None
    in_rate, out_rate = rate
    return (input_tokens / 1_000_000) * in_rate + (output_tokens / 1_000_000) * out_rate


def blended_cost_usd(
    input_tokens: int,
    output_tokens: int,
    *,
    debate_model: str,
    arbitrator_model: str,
    gatekeeper_model: str,
) -> float | None:
    """Approximate a run's cost when tokens aren't attributed per model.

    The token accumulator (`token_totals`) sums across every role in a run and
    does not split tokens by model. For an honest single number we price the
    whole run at the debater model's rate — it's the dominant contributor (all
    three debaters + moderator routing) and the mid-tier rate, so it neither
    flatters nor inflates the society. Returns None if that rate is unverified.

    The per-model detail (which role ran which model) is still logged in the JSON
    so the estimate can be refined later without re-running.
    """
    del arbitrator_model, gatekeeper_model  # documented; not used in the blend
    return cost_usd(debate_model, input_tokens, output_tokens)
