# Agent Society vs. Single-Agent Baseline

_Generated 2026-07-07T17:36:53.722252+00:00. 19 labeled cases, identical RAG corpus per professor, same retrieval tool available to both paths._

## Headline

On 19 labeled cases, the single-agent baseline scored 84% accuracy and let 2 fabricated/inflated-claim case(s) through; the society scored 90% and let 1 through — catching 1 the baseline missed, at 5.9× the tokens (620,795 vs 104,895).

The society is **not** cheaper or faster — it spends more tokens and wall-clock to buy accuracy on exactly the cases a lone agent rubber-stamps. That trade is the point.

## Summary

| Metric | Single-agent | Society |
| :-- | --: | --: |
| Accuracy | 84% | 90% |
| Correct / 19 | 16 | 17 |
| False accepts (trap missed) | 2 | 1 |
| Total tokens | 104,895 | 620,795 |
| Total LLM calls | 45 | 300 |
| Total latency (s) | 530.0 | 1265.5 |
| Est. cost (USD) | N/A | N/A |

## Per-case

| Case | Failure mode | Truth | Baseline | Society |
| :-- | :-- | :-- | :-- | :-- |
| mata-fab-1 | fabricated_citation | decline | decline ✓ | decline ✓ |
| mata-fab-2 | fabricated_citation | decline | decline ✓ | decline ✓ |
| mata-inflated-1 | inflated_alignment | decline | decline ✓ | decline ✓ |
| mata-inflated-2 | inflated_alignment | request_more_info | request_more_info ✓ | request_more_info ✓ |
| mata-strong-1 | clean_strong_fit | invite | invite ✓ | request_more_info ✗ |
| mata-strong-2 | clean_strong_fit | invite | invite ✓ | request_more_info ✗ |
| mata-weak-1 | clean_weak_fit | decline | decline ✓ | decline ✓ |
| mata-weak-2 | clean_weak_fit | decline | decline ✓ | decline ✓ |
| mata-inflated-3 | inflated_alignment | decline | decline ✓ | decline ✓ |
| okoye-cap-1 | capacity_mismatch | request_more_info | request_more_info ✓ | request_more_info ✓ |
| okoye-cap-2 | capacity_mismatch | request_more_info | invite ✗ | request_more_info ✓ |
| okoye-fab-1 | fabricated_citation | decline | decline ✓ | decline ✓ |
| okoye-inflated-1 | inflated_alignment | decline | decline ✓ | decline ✓ |
| okoye-weak-1 | clean_weak_fit | decline | decline ✓ | decline ✓ |
| okoye-cap-3 | capacity_mismatch | request_more_info | request_more_info ✓ | request_more_info ✓ |
| mata-hard-contradiction | hard_buried_contradiction | decline | decline ✓ | decline ✓ |
| mata-hard-false-extension | hard_false_extension | decline | invite ✗ | decline ✓ |
| okoye-hard-funding | hard_funding_override | request_more_info | invite ✗ | request_more_info ✓ |
| okoye-hard-value-inversion | hard_value_inversion | decline | decline ✓ | decline ✓ |

> Cost is estimated at the debater-tier rate on the Singapore endpoint; unpriced models report N/A. See `pricing.py` — verify rates against the live pricing page before quoting dollar figures.
