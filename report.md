# Decision model comparison on real data

Items scored: 1185 (only items every model answered without an API error; refusals count as wrong). Data created after 2026-09-15; ground truth = maintainers' real decisions.

## Overall (mean over tasks)

| Model | Mean accuracy | Mean Brier (lower better) | Mean ECE (lower better) | p50 latency | p95 latency | Cost / 1k decisions | API errors |
|---|---|---|---|---|---|---|---|
| liquid/d1-ultra | 73.8% | 0.329 | 0.050 | 533 ms | 1184 ms | $0.0240 | 0/1185 |
| perplexity/pplx-decider-v1.2 | 73.2% | 0.355 | 0.101 | 643 ms | 994 ms | $0.0126 | 0/1185 |
| nace-ai/drex-max | 73.1% | 0.370 | 0.117 | 745 ms | 1158 ms | $0.0381 | 0/1185 |
| typesafe/jev-1.13 | 72.2% | 0.383 | 0.112 | 704 ms | 803 ms | $0.0368 | 0/1185 |
| typesafe/jev-1.14 | 72.0% | 0.386 | 0.120 | 696 ms | 801 ms | $0.0368 | 0/1185 |
| openai/gpt-6-luna-decisions | 70.6% | 0.432 | 0.174 | 633 ms | 1021 ms | $0.0632 | 0/1185 |
| liquid/d1.1 | 69.8% | 0.403 | 0.097 | 422 ms | 534 ms | $0.0114 | 0/1185 |

## A. VS Code issue: bug vs feature

| Model | Accuracy (95% CI) | Macro-F1 | AUC | Brier | Log loss | ECE | Acc. when >=90% sure | Share >=90% sure | Refusals | vs drex-max (p) |
|---|---|---|---|---|---|---|---|---|---|---|
| liquid/d1-ultra | 92.0% (89%-95%) | 0.920 | 0.976 | 0.114 | 0.201 | 0.026 | 97.7% | 71.0% | 0 | 0.754 |
| perplexity/pplx-decider-v1.2 | 91.7% (89%-95%) | 0.917 | 0.978 | 0.112 | 0.195 | 0.029 | 97.5% | 78.7% | 0 | 0.375 |
| nace-ai/drex-max | 92.7% (90%-95%) | 0.927 | 0.979 | 0.105 | 0.191 | 0.024 | 97.5% | 81.3% | 0 | - |
| typesafe/jev-1.13 | 92.0% (89%-95%) | 0.920 | 0.972 | 0.125 | 0.227 | 0.044 | 97.3% | 62.7% | 0 | 0.804 |
| typesafe/jev-1.14 | 91.7% (88%-95%) | 0.917 | 0.974 | 0.128 | 0.230 | 0.055 | 98.3% | 59.3% | 0 | 0.607 |
| openai/gpt-6-luna-decisions | 91.0% (88%-94%) | 0.910 | 0.972 | 0.129 | 0.249 | 0.019 | 97.0% | 76.7% | 0 | 0.383 |
| liquid/d1.1 | 92.7% (90%-95%) | 0.927 | 0.976 | 0.117 | 0.206 | 0.033 | 98.5% | 67.0% | 0 | 1.000 |

n = 300

## B. PR will be merged

| Model | Accuracy (95% CI) | Macro-F1 | AUC | Brier | Log loss | ECE | Acc. when >=90% sure | Share >=90% sure | Refusals | vs drex-max (p) |
|---|---|---|---|---|---|---|---|---|---|---|
| liquid/d1-ultra | 68.3% (63%-74%) | 0.667 | 0.767 | 0.409 | 0.594 | 0.054 | 95.8% | 8.0% | 0 | 0.542 |
| perplexity/pplx-decider-v1.2 | 64.3% (59%-70%) | 0.596 | 0.774 | 0.537 | 0.815 | 0.237 | 74.5% | 51.0% | 0 | 0.118 |
| nace-ai/drex-max | 66.7% (61%-72%) | 0.630 | 0.794 | 0.526 | 0.850 | 0.223 | 73.6% | 69.3% | 0 | - |
| typesafe/jev-1.13 | 60.0% (55%-66%) | 0.540 | 0.634 | 0.493 | 0.688 | 0.088 | 100.0% | 0.3% | 0 | 0.001 |
| typesafe/jev-1.14 | 58.7% (53%-64%) | 0.508 | 0.620 | 0.511 | 0.708 | 0.113 | 100.0% | 0.7% | 0 | 0.000 |
| openai/gpt-6-luna-decisions | 57.0% (51%-63%) | 0.486 | 0.690 | 0.537 | 0.744 | 0.195 | 90.0% | 3.3% | 0 | 0.000 |
| liquid/d1.1 | 57.7% (52%-63%) | 0.507 | 0.641 | 0.543 | 0.755 | 0.179 | 85.7% | 2.3% | 0 | 0.000 |

n = 300

## C. Firefox bug -> component (8)

| Model | Accuracy (95% CI) | Macro-F1 | Brier | Log loss | ECE | Acc. when >=90% sure | Share >=90% sure | Refusals | vs drex-max (p) |
|---|---|---|---|---|---|---|---|---|---|
| liquid/d1-ultra | 89.8% (87%-93%) | 0.903 | 0.153 | 0.300 | 0.035 | 99.0% | 68.3% | 0 | 0.035 |
| perplexity/pplx-decider-v1.2 | 88.1% (84%-91%) | 0.886 | 0.174 | 0.327 | 0.034 | 97.6% | 70.6% | 0 | 0.388 |
| nace-ai/drex-max | 86.7% (83%-90%) | 0.874 | 0.202 | 0.385 | 0.065 | 93.4% | 82.3% | 0 | - |
| typesafe/jev-1.13 | 89.4% (86%-92%) | 0.901 | 0.172 | 0.506 | 0.063 | 95.8% | 80.9% | 0 | 0.096 |
| typesafe/jev-1.14 | 89.1% (85%-92%) | 0.899 | 0.175 | 0.409 | 0.047 | 94.9% | 80.2% | 0 | 0.143 |
| openai/gpt-6-luna-decisions | 87.0% (83%-91%) | 0.885 | 0.203 | 0.639 | 0.073 | 93.0% | 83.3% | 5 | 1.000 |
| liquid/d1.1 | 86.3% (82%-90%) | 0.869 | 0.202 | 0.410 | 0.060 | 94.0% | 74.1% | 0 | 1.000 |

n = 293

## D. Firefox bug severity (S1-S4)

| Model | Accuracy (95% CI) | Macro-F1 | MAE | Within 1 | Spearman | Brier | Log loss | ECE | Acc. when >=90% sure | Share >=90% sure | Refusals | vs drex-max (p) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| liquid/d1-ultra | 45.2% (40%-51%) | 0.315 | 0.61 | 94.5% | 0.150 | 0.640 | 1.155 | 0.084 | 75.0% | 1.4% | 0 | 0.659 |
| perplexity/pplx-decider-v1.2 | 48.6% (42%-55%) | 0.313 | 0.56 | 95.9% | 0.202 | 0.599 | 1.002 | 0.104 | 80.0% | 1.7% | 0 | 0.362 |
| nace-ai/drex-max | 46.6% (41%-52%) | 0.307 | 0.57 | 96.9% | 0.157 | 0.646 | 1.097 | 0.157 | 88.9% | 3.1% | 0 | - |
| typesafe/jev-1.13 | 47.3% (42%-53%) | 0.341 | 0.64 | 91.8% | 0.192 | 0.743 | 2.328 | 0.252 | 50.0% | 22.6% | 0 | 0.897 |
| typesafe/jev-1.14 | 48.6% (43%-55%) | 0.352 | 0.61 | 93.2% | 0.219 | 0.729 | 1.978 | 0.266 | 55.6% | 21.6% | 0 | 0.519 |
| openai/gpt-6-luna-decisions | 47.3% (42%-53%) | 0.264 | 0.57 | 96.2% | 0.276 | 0.858 | 3.192 | 0.408 | 51.4% | 62.0% | 0 | 0.917 |
| liquid/d1.1 | 42.5% (37%-49%) | 0.324 | 0.75 | 88.0% | -0.006 | 0.748 | 1.541 | 0.114 | 50.0% | 1.4% | 0 | 0.148 |

n = 292

## How to read this

- **Brier / log loss / ECE**: quality of the probabilities. Lower is better. ECE = gap between stated confidence and actual accuracy.
- **Acc. when >=90% sure**: how often the model is right when it says it is at least 90% sure; *Share* = how often it says that.
- **p** column: exact McNemar test of each model's per-item correctness against nace-ai/drex-max; p < 0.05 = the accuracy gap is unlikely to be chance.
- Providers: liquid/d1-ultra: Liquid; perplexity/pplx-decider-v1.2: Makora, Perplexity; nace-ai/drex-max: DeepInfra; typesafe/jev-1.13: TypeSafe; typesafe/jev-1.14: TypeSafe; openai/gpt-6-luna-decisions: OpenAI; liquid/d1.1: Liquid
