# Total score (SCORING.md)

| Rank | Model | **Total** (95% CI) | Quality 45% | Efficiency 20% | Trust 20% | Reviews 10% | Signup bonus 5% | Wins under random weights |
|---|---|---|---|---|---|---|---|---|
| 1 | perplexity/pplx-decider-v1.2 | **59.2** (58.5-59.9) | 47.8 | 62.1 | 99.3 | 53.9 | 0.0 | 33% |
| 2 | nace-ai/drex-max | **54.9** (54.2-55.6) | 46.6 | 48.4 | 79.8 | 40.0 | 85.7 | 47% |
| 3 | liquid/d1-ultra | **49.7** (49.0-50.5) | 49.2 | 55.6 | 43.1 | 40.2 | 76.6 | 1% |
| 4 | typesafe/jev-1.13 | **49.4** (48.6-50.1) | 44.8 | 49.7 | 62.3 | 68.1 | 0.0 | 5% |
| 5 | typesafe/jev-1.14 | **49.3** (48.5-50.0) | 44.8 | 50.0 | 64.2 | 63.1 | 0.0 | 0% |
| 6 | liquid/d1.1 | **49.1** (48.4-49.7) | 44.7 | 66.0 | 38.2 | 39.9 | 82.0 | 15% |
| 7 | openai/gpt-6-luna-decisions | **39.1** (38.4-39.8) | 41.0 | 41.4 | 39.9 | 43.7 | 0.0 | 0% |

**Verdict (pre-registered rule):** No model is best overall. perplexity/pplx-decider-v1.2 is #1 under the main weights but wins only 33% of random weightings, so the winner depends on what you value.

## Does the ranking depend on the weights?

| Scenario | #1 | #2 | #3 |
|---|---|---|---|
| Main weights (45/20/20/10/5) | pplx-decider-v1.2 | drex-max | d1-ultra |
| Quality only | d1-ultra | pplx-decider-v1.2 | drex-max |
| Equal weights (20% each) | drex-max | d1.1 | d1-ultra |
| No signup bonus (rescaled) | pplx-decider-v1.2 | drex-max | jev-1.13 |
| Drex Max at list price (no 50% promo) | pplx-decider-v1.2 | drex-max | d1-ultra |

## Inputs

Discussion (Hacker News since 2026-09-01, relevant mentions; <10 = neutral 50): jev: n=247 (+71/-37); liquid-d1: n=8 (+1/-1) insufficient; decider: n=8 (+2/-1) insufficient; luna-decisions: n=13 (+3/-4); drex: n=1 (+1/-0) insufficient

Free decisions from signup credit (provider's own price, 1,200-token request): d1-ultra 39,682, d1.1 83,333, drex-max 138,888, gpt-6-luna-decisions 0, pplx-decider-v1.2 0, jev-1.13 0, jev-1.14 0
