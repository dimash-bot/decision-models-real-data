# Decision models on real tech data: full report (v2, 2026-11-06)

Disclosure: the author works at Nace.AI (Drex). Method pre-registered: see METHODOLOGY.md, SCORING.md and PREREGISTRATION.txt (checksums and freeze times).

Deviations from the pre-registration: (1) Amendment 1 added T6 (NVD feed) before any model call. (2) Exploratory, not pre-registered: the T3 subset whose title doesn't name the component, and random weights without the bonus pillar (total_score_exploratory.txt). (3) Reliability in the Trust score is measured after retries, as specified; d1-ultra's ~1.8% first-attempt timeouts are therefore not penalised there and are reported separately.


Items per task: {'T1': 547, 'T2': 472, 'T3': 534, 'T4': 292, 'T5': 480, 'T6': 500}. Dropped for API errors: 1. Each item asked in 3 phrasings.

## Overall: mean balanced accuracy over all tasks

| Rank | Model | Balanced acc. (95% CI) | P(rank #1) | Rank 95% CI | Mean Brier | Mean ECE | p50 / p95 latency | Cost / 1k | Same answer on repeat |
|---|---|---|---|---|---|---|---|---|---|
| 1 | liquid/d1-ultra | 66.1% (64.6%-67.6%) | 81% | 1-3 | 0.426 | 0.067 | 682 / 5139 ms | $0.0335 | 95.7% |
| 2 | perplexity/pplx-decider-v1.2 | 65.6% (64.2%-67.0%) | 18% | 1-3 | 0.433 | 0.099 | 784 / 1318 ms | $0.0182 | 99.3% |
| 3 | nace-ai/drex-max | 64.9% (63.5%-66.3%) | 1% | 2-5 | 0.450 | 0.117 | 731 / 1198 ms | $0.0549 | 97.3% |
| 4 | typesafe/jev-1.13 | 64.2% (62.7%-65.7%) | 0% | 3-6 | 0.486 | 0.148 | 699 / 885 ms | $0.0515 | 97.3% |
| 5 | typesafe/jev-1.14 | 64.2% (62.6%-65.7%) | 0% | 3-6 | 0.481 | 0.144 | 678 / 756 ms | $0.0515 | 99.2% |
| 6 | liquid/d1.1 | 63.7% (62.3%-65.1%) | 0% | 4-7 | 0.477 | 0.102 | 632 / 746 ms | $0.0160 | 90.7% |
| 7 | openai/gpt-6-luna-decisions | 62.8% (61.5%-64.2%) | 0% | 6-7 | 0.564 | 0.233 | 758 / 1078 ms | $0.0915 | 100.0% |

**Verdict (pre-registered rule):** no single best model; statistically tied top group: liquid/d1-ultra, perplexity/pplx-decider-v1.2, nace-ai/drex-max.

## T1. Bug report or feature request (GitHub issues) (n = 547)

Baselines: always-majority 50.0%; shortcut rule 69.9%

| Model | Balanced acc. (95% CI) | P1 / P2 / P3 | Macro-F1 | AUC | Brier | ECE | Acc. when >=90% sure (share) | Refusals |
|---|---|---|---|---|---|---|---|---|
| nace-ai/drex-max | 92.4% (90.1%-94.3%) | 92% / 93% / 93% | 0.924 | 0.975 | 0.111 | 0.029 | 96.6% (84%) | 0.0 |
| liquid/d1.1 | 92.3% (89.9%-94.3%) | 92% / 93% / 92% | 0.923 | 0.970 | 0.124 | 0.025 | 97.4% (70%) | 0.0 |
| liquid/d1-ultra | 92.2% (89.9%-94.2%) | 92% / 92% / 93% | 0.922 | 0.972 | 0.120 | 0.024 | 97.7% (71%) | 0.0 |
| perplexity/pplx-decider-v1.2 | 92.1% (89.8%-94.3%) | 92% / 92% / 92% | 0.921 | 0.975 | 0.116 | 0.029 | 96.7% (80%) | 0.0 |
| openai/gpt-6-luna-decisions | 90.8% (88.5%-92.9%) | 91% / 91% / 91% | 0.908 | 0.959 | 0.150 | 0.035 | 94.8% (78%) | 0.0 |
| typesafe/jev-1.14 | 90.5% (88.0%-92.7%) | 91% / 91% / 90% | 0.905 | 0.966 | 0.150 | 0.045 | 96.7% (58%) | 0.0 |
| typesafe/jev-1.13 | 90.3% (87.9%-92.5%) | 91% / 90% / 90% | 0.903 | 0.965 | 0.145 | 0.044 | 96.5% (60%) | 0.0 |

Top group (not significantly different from #1 after Holm): drex-max, d1.1, d1-ultra, pplx-decider-v1.2, gpt-6-luna-decisions, jev-1.14, jev-1.13

## T2. Will this PR be merged (GitHub PRs) (n = 472)

Baselines: always-majority 50.0%; shortcut rule 73.1%

| Model | Balanced acc. (95% CI) | P1 / P2 / P3 | Macro-F1 | AUC | Brier | ECE | Acc. when >=90% sure (share) | Refusals |
|---|---|---|---|---|---|---|---|---|
| liquid/d1-ultra | 63.6% (60.2%-66.8%) | 62% / 67% / 63% | 0.620 | 0.719 | 0.439 | 0.051 | 100.0% (3%) | 0.0 |
| perplexity/pplx-decider-v1.2 | 60.7% (58.0%-63.3%) | 61% / 60% / 61% | 0.544 | 0.705 | 0.578 | 0.237 | 68.7% (37%) | 0.0 |
| nace-ai/drex-max | 59.8% (57.1%-62.6%) | 60% / 58% / 62% | 0.537 | 0.706 | 0.634 | 0.291 | 67.2% (62%) | 0.0 |
| liquid/d1.1 | 58.2% (55.8%-60.5%) | 59% / 59% / 57% | 0.501 | 0.619 | 0.576 | 0.198 | 85.7% (9%) | 0.0 |
| typesafe/jev-1.13 | 58.0% (55.6%-60.4%) | 58% / 60% / 56% | 0.502 | 0.656 | 0.520 | 0.130 | 100.0% (0%) | 0.0 |
| openai/gpt-6-luna-decisions | 57.5% (55.2%-59.9%) | 57% / 58% / 57% | 0.490 | 0.650 | 0.540 | 0.165 | 86.4% (3%) | 0.0 |
| typesafe/jev-1.14 | 56.4% (54.3%-58.6%) | 57% / 57% / 56% | 0.470 | 0.644 | 0.533 | 0.150 | 100.0% (0%) | 0.0 |

Top group (not significantly different from #1 after Holm): d1-ultra, pplx-decider-v1.2, drex-max

## T3. Firefox bug -> component (all components) (n = 534)

Baselines: always-majority 2.6%; shortcut rule 20.6%

| Model | Balanced acc. (95% CI) | P1 / P2 / P3 | Macro-F1 | Brier | ECE | Acc. when >=90% sure (share) | Refusals |
|---|---|---|---|---|---|---|---|
| perplexity/pplx-decider-v1.2 | 77.6% (74.3%-80.7%) | 77% / 78% / 77% | 0.780 | 0.320 | 0.036 | 96.4% (41%) | 0.0 |
| nace-ai/drex-max | 76.4% (73.2%-79.6%) | 76% / 77% / 76% | 0.767 | 0.347 | 0.088 | 92.6% (57%) | 0.0 |
| liquid/d1-ultra | 76.4% (73.3%-79.5%) | 76% / 77% / 76% | 0.762 | 0.347 | 0.046 | 96.1% (26%) | 0.0 |
| openai/gpt-6-luna-decisions | 74.9% (71.5%-78.2%) | 74% / 75% / 75% | 0.755 | 0.418 | 0.155 | 82.7% (74%) | 1.3 |
| typesafe/jev-1.14 | 72.7% (69.2%-76.0%) | 73% / 73% / 73% | 0.734 | 0.397 | 0.105 | 89.5% (52%) | 0.0 |
| liquid/d1.1 | 72.6% (69.4%-75.8%) | 72% / 74% / 72% | 0.724 | 0.396 | 0.042 | 93.3% (32%) | 0.0 |
| typesafe/jev-1.13 | 72.3% (68.8%-75.7%) | 72% / 73% / 72% | 0.729 | 0.411 | 0.136 | 87.2% (60%) | 0.0 |

Top group (not significantly different from #1 after Holm): pplx-decider-v1.2, drex-max, d1-ultra, gpt-6-luna-decisions

## T4. Firefox bug severity (S4-S1) (n = 292)

Baselines: always-majority 33.3%

| Model | Balanced acc. (95% CI) | P1 / P2 / P3 | Macro-F1 | QWK | Within 1 | Brier | ECE | Acc. when >=90% sure (share) | Refusals |
|---|---|---|---|---|---|---|---|---|---|
| typesafe/jev-1.14 | 47.1% (40.9%-53.3%) | 46% / 44% / 51% | 0.486 | 0.247 | 93.9% | 0.704 | 0.240 | 53.6% (25%) | 0.0 |
| typesafe/jev-1.13 | 45.0% (39.1%-51.0%) | 42% / 43% / 51% | 0.457 | 0.223 | 92.6% | 0.727 | 0.247 | 50.8% (23%) | 0.0 |
| liquid/d1-ultra | 44.2% (38.6%-50.0%) | 43% / 44% / 46% | 0.426 | 0.252 | 97.6% | 0.645 | 0.081 | 100.0% (0%) | 0.0 |
| perplexity/pplx-decider-v1.2 | 43.3% (38.5%-48.5%) | 41% / 40% / 48% | 0.433 | 0.310 | 98.2% | 0.582 | 0.108 | 100.0% (1%) | 0.0 |
| liquid/d1.1 | 42.5% (36.6%-48.2%) | 42% / 43% / 42% | 0.430 | 0.031 | 90.8% | 0.701 | 0.131 | 81.5% (2%) | 0.0 |
| nace-ai/drex-max | 42.4% (37.2%-47.5%) | 42% / 40% / 45% | 0.436 | 0.199 | 95.8% | 0.628 | 0.119 | 69.6% (5%) | 0.0 |
| openai/gpt-6-luna-decisions | 39.7% (35.3%-44.2%) | 39% / 40% / 40% | 0.395 | 0.240 | 96.5% | 0.845 | 0.396 | 51.6% (61%) | 0.0 |

Top group (not significantly different from #1 after Holm): jev-1.14, jev-1.13, d1-ultra, pplx-decider-v1.2, d1.1, drex-max, gpt-6-luna-decisions

## T5. Security advisory severity (low-critical) (n = 480)

Baselines: always-majority 25.0%

| Model | Balanced acc. (95% CI) | P1 / P2 / P3 | Macro-F1 | QWK | Within 1 | Brier | ECE | Acc. when >=90% sure (share) | Refusals |
|---|---|---|---|---|---|---|---|---|---|
| liquid/d1-ultra | 45.1% (41.5%-49.0%) | 45% / 44% / 46% | 0.419 | 0.580 | 92.1% | 0.674 | 0.140 | 100.0% (4%) | 0.0 |
| nace-ai/drex-max | 44.7% (40.8%-48.7%) | 45% / 45% / 44% | 0.438 | 0.576 | 92.6% | 0.649 | 0.122 | 100.0% (4%) | 0.0 |
| liquid/d1.1 | 43.9% (40.3%-47.4%) | 44% / 43% / 44% | 0.397 | 0.546 | 91.5% | 0.700 | 0.155 | 100.0% (4%) | 0.0 |
| typesafe/jev-1.13 | 43.8% (40.1%-47.5%) | 45% / 43% / 43% | 0.407 | 0.484 | 87.3% | 0.792 | 0.271 | 89.6% (11%) | 0.0 |
| perplexity/pplx-decider-v1.2 | 43.7% (40.1%-47.5%) | 44% / 44% / 44% | 0.407 | 0.569 | 93.9% | 0.675 | 0.125 | 100.0% (2%) | 0.0 |
| typesafe/jev-1.14 | 43.6% (39.9%-47.4%) | 44% / 44% / 43% | 0.406 | 0.479 | 87.4% | 0.780 | 0.267 | 90.6% (10%) | 0.0 |
| openai/gpt-6-luna-decisions | 38.3% (35.0%-41.9%) | 39% / 38% / 38% | 0.340 | 0.535 | 94.8% | 1.056 | 0.496 | 40.3% (61%) | 0.0 |

Top group (not significantly different from #1 after Holm): d1-ultra, drex-max, d1.1, jev-1.13, pplx-decider-v1.2, jev-1.14

## T6. CVE weakness type (20 CWEs, NVD feed) (n = 500)

Baselines: always-majority 5.0%

| Model | Balanced acc. (95% CI) | P1 / P2 / P3 | Macro-F1 | Brier | ECE | Acc. when >=90% sure (share) | Refusals |
|---|---|---|---|---|---|---|---|
| perplexity/pplx-decider-v1.2 | 76.0% (73.1%-79.1%) | 76% / 77% / 76% | 0.756 | 0.327 | 0.057 | 99.5% (40%) | 0.0 |
| openai/gpt-6-luna-decisions | 75.9% (72.8%-78.9%) | 78% / 76% / 74% | 0.763 | 0.377 | 0.151 | 87.6% (76%) | 0.0 |
| typesafe/jev-1.13 | 75.8% (72.9%-78.7%) | 77% / 76% / 75% | 0.755 | 0.319 | 0.060 | 95.6% (59%) | 0.0 |
| liquid/d1-ultra | 75.1% (72.3%-77.7%) | 75% / 75% / 75% | 0.724 | 0.333 | 0.058 | 97.3% (40%) | 0.0 |
| typesafe/jev-1.14 | 74.8% (71.7%-77.8%) | 75% / 75% / 75% | 0.747 | 0.320 | 0.059 | 95.8% (57%) | 0.0 |
| nace-ai/drex-max | 73.9% (71.1%-77.0%) | 74% / 74% / 74% | 0.725 | 0.334 | 0.051 | 97.5% (56%) | 0.0 |
| liquid/d1.1 | 72.7% (69.8%-75.8%) | 73% / 72% / 72% | 0.728 | 0.364 | 0.062 | 99.1% (31%) | 0.0 |

Top group (not significantly different from #1 after Holm): pplx-decider-v1.2, gpt-6-luna-decisions, jev-1.13, d1-ultra, jev-1.14, drex-max, d1.1

## Significant pairwise differences, overall (Holm-adjusted p < 0.05)

- d1-ultra > gpt-6-luna-decisions by 3.3 pts (adj. p = 0.000)
- pplx-decider-v1.2 > gpt-6-luna-decisions by 2.7 pts (adj. p = 0.000)
- d1-ultra > d1.1 by 2.4 pts (adj. p = 0.000)
- drex-max > gpt-6-luna-decisions by 2.1 pts (adj. p = 0.018)
- d1-ultra > jev-1.14 by 1.9 pts (adj. p = 0.030)
- d1-ultra > jev-1.13 by 1.9 pts (adj. p = 0.018)
- pplx-decider-v1.2 > d1.1 by 1.9 pts (adj. p = 0.018)

## Data quality

- Items where all 7 models agree with each other but not with the label: 381 {'T1': 28, 'T2': 121, 'T3': 50, 'T4': 53, 'T5': 106, 'T6': 23} (label_audit.csv, for human review).
- T4: share of bugs whose severity was later changed by triagers: 2.7%.
- T3 exploratory (not pre-registered): balanced accuracy on the 433 bugs whose title does not name the component: pplx-decider-v1.2 73.8%, d1-ultra 72.6%, drex-max 72.2%, gpt-6-luna-decisions 71.6%, d1.1 69.2%, jev-1.14 69.1%, jev-1.13 68.8%


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

## Exploratory: random weightings without the signup bonus

```
no bonus {'pplx-decider-v1.2': '87%', 'jev-1.13': '12%', 'd1.1': '1%', 'd1-ultra': '0%'}
quality+efficiency+trust only {'pplx-decider-v1.2': '96%', 'd1.1': '3%', 'd1-ultra': '0%'}
quality+efficiency only {'d1.1': '56%', 'pplx-decider-v1.2': '27%', 'd1-ultra': '17%'}
```

## Pricing, deals, openness and data policy

Checked 2026-11-06. To keep this objective, the same two sources are used for every company, and
no company's own marketing, docs or blog posts are used (including Nace's):

- **OpenRouter** public data: `api/v1/models/<id>/endpoints` (price, discount, cache price, context,
  host) and each model page's `dataPolicy` record (training, prompt retention, zero-data-retention).
  Raw copy: `openrouter_endpoints.json`.
- **Hugging Face** model metadata and the licence files themselves. Raw copy: `huggingface.json`.

Prices are what you pay through OpenRouter, per 1M input tokens. Every model charges $0 for output.

### A. Pricing and deals (OpenRouter)

| Model | Host on OpenRouter | Price / 1M input | Cache-read price | Current discount | Context |
|---|---|---|---|---|---|
| TypeSafe Jev 1.14 | TypeSafe | $0.042 | no caching | none | 262K |
| TypeSafe Jev 1.13 | TypeSafe | $0.042 | no caching | none | 262K |
| Perplexity Decider V1.2 | Makora (fp16) / Perplexity | $0.019 / $0.020 | no caching | none | 262K |
| Liquid d1-ultra | Liquid | $0.042 | $0.042 (no saving) | none | 33K |
| Liquid d1.1 | Liquid | $0.020 | $0.020 (no saving) | none | 66K |
| OpenAI GPT-6 Luna Decisions | OpenAI | $0.100 | $0 (cached input free) | none | 1.05M |
| Nace Drex Max | DeepInfra | $0.060 | $0.060 (no saving) | **50% off** (list $0.12, no end date shown) | 262K |

Notes: Drex Max's price is a temporary discount; at list price ($0.12) it would be the most expensive
model here. GPT-6 Luna is the only one where repeated input (cache) is actually cheaper.

### B. Openness and data policy

| Model | Weights on Hugging Face | Licence | Size / base model (per HF metadata) | Trains on your prompts (OpenRouter) | Keeps your prompts (OpenRouter) | Zero-data-retention available |
|---|---|---|---|---|---|---|
| Jev 1.13 / 1.14 | No | — | not public | No | No | Yes |
| Decider V1.2 | Yes (`perplexity-ai/pplx-decider-v1.2`) | Apache-2.0 (no commercial limits) | 26.1B, `Qwen/Qwen3.8-27B` | No | No | Yes |
| d1-ultra / d1.1 | Not these models. Smaller relatives are open (`LiquidAI/d1-2B`, `d1-3B`) | LFM Open License v1.0: commercial licence needed at ≥ $10M annual revenue | API models: not public. HF d1-3B: 3.1B on `LFM2.5-VL-3B` | **Conflicting**: provider record says yes, endpoint record says no | **Conflicting** (same) | Yes |
| GPT-6 Luna Decisions | No | — | not public | No | **Yes** | **No** |
| Drex Max | `nace-ai/drex-max-v1` (OpenRouter serves version `20261016`; HF doesn't say if it's the same) | Nace.AI Open RAIL-M: commercial licence needed if your org had > $1M revenue in the last 12 months **or** raised > $1M | 26.1B; base model **not stated** | No | No | Yes |

Observation, not a conclusion: Hugging Face reports exactly the same parameter count
(26,085,330,160) for `nace-ai/drex-max-v1` and for Perplexity's Decider models, which state
`Qwen/Qwen3.8-27B` as their base. Drex Max's card names no base model.

### What this means for a developer
- **Cheapest:** Decider V1.2 ($0.019) and d1.1 ($0.020).
- **Most open:** Decider V1.2: weights published under Apache-2.0 with no revenue limits.
- **Most private by default (per OpenRouter):** Jev, Decider and Drex Max: no training, no prompt
  retention, zero-data-retention available. GPT-6 Luna keeps prompts and has no ZDR option on
  OpenRouter. Liquid's record on OpenRouter is self-contradictory; check before sending sensitive data.
- **Licence limits:** Drex Max's open weights need a commercial licence for any org with more than
  $1M revenue or funding; Liquid's open d1 models need one at $10M revenue; Perplexity's need none.

## Exploratory: direct-API prices (added after the run)

All costs above are what OpenRouter billed. Each provider's own price list (checked 2026-11-06) matches its
OpenRouter price, except Nace: Drex Max is $0.03 per 1M input tokens on Nace's API versus $0.06 on OpenRouter
(itself 50% off a $0.12 list price). Re-scoring with every model at its own direct price changes only Drex Max:
cost ~$0.027 per 1k decisions (from $0.055), efficiency 57.5 (from 48.4), total 56.7 (from 54.9), still #2;
Decider stays #1 at 59.1. Random weightings: all pillars, Drex Max 59% / Decider 28%; without the bonus pillar,
Decider 86% / Jev 1.13 13% / Drex Max 0%. Direct APIs were not tested; this assumes the same model is served.

## Amendment 2 (2026-11-07, after the main results): Drex Max v1.1 on Nace's API

At a reviewer's request the Drex Max entry was re-tested as **drex-max-v1.1** (released 2026-10-28) on
Nace's own API (`https://console.nace.ai/v1/systemone`), with the same 2,826 items, the same three
phrasings and the same repeat check. OpenRouter serves drex-max-20261016 (v1.0); those results are kept in
`results_archive/nace-ai__drex-max-v1.0-openrouter.jsonl`. This changes one model after results were
known, which the pre-registration did not anticipate; it is reported here rather than hidden.

- Cost uses Nace's list price ($0.03 per 1M input tokens, from reported input tokens); trust uses Nace's
  terms (no training by default; Standard mode keeps job inputs until deletion, unclear for decision
  requests -> half points; zero retention available) and Hugging Face (only drex-max-v1 is published).
- Nace's API rejected one advisory (GHSA-r543-q48m-4c9j) whose text embeds an image as a data URL
  (HTTP 422); per the pre-registered rule it is dropped for every model (2 items dropped in total).
- Result: v1.1 balanced accuracy 65.6% (v1.0: 64.9%), still in the tied top group with d1-ultra and
  Decider; overconfidence +4.6 points (v1.0: +10.4); p95 latency 833 ms; total score 53.0, #2 (v1.0: 54.9;
  lower trust score). Decider remains #1 (59.2). Average confidence vs share right is in `confidence.json`
  (reviewer request, replacing the 90%-confidence view in the post).
