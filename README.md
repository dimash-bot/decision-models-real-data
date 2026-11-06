# Decision models on real tech data

Seven OpenRouter decision models (TypeSafe Jev 1.13/1.14, Perplexity Decider V1.2, Liquid d1-ultra and d1.1,
OpenAI GPT-6 Luna Decisions, Nace Drex Max) tested on 2,826 real software-engineering decisions, plus a
total score covering efficiency, trust, reviews and signup bonuses.

**Disclosure:** the author works at Nace.AI, which makes Drex Max. The method, prompts and scoring formula
were fixed and checksummed before any model was run (`v2/PREREGISTRATION.txt`); every model got identical
inputs through OpenRouter; all data, raw outputs and code are here so anyone can re-score it.

## Start here

| File | What it is |
|---|---|
| [`v2/REPORT.md`](v2/REPORT.md) | Full results: every task, metric, significance test, total score and deviation |
| [`v2/METHODOLOGY.md`](v2/METHODOLOGY.md) | Pre-registered method (+ Amendment 1, added before any model call) |
| [`v2/SCORING.md`](v2/SCORING.md) | Pre-registered total-score formula and weights |
| [`v2/PREREGISTRATION.txt`](v2/PREREGISTRATION.txt) | Freeze times and SHA-256 checksums |
| [`v2/company/COMPANY_COMPARISON.md`](v2/company/COMPANY_COMPARISON.md) | Pricing, openness, data policy (OpenRouter + Hugging Face only) |
| [`v2/label_audit.csv`](v2/label_audit.csv) | 381 items where all 7 models agree with each other but not with the label |

## Headline

- **Accuracy:** d1-ultra 66.1%, Drex Max v1.1 65.6% and Decider 65.6% are statistically tied for first;
  GPT-6 Luna (62.8%) is significantly behind all three.
- **Total score:** Decider 59.2, Drex Max v1.1 53.0, d1-ultra 49.7 … Luna 39.1. By the pre-registered rule no model
  is best overall; Drex Max's share of random-weight wins comes entirely from its signup bonus.

## Data (v2, all created after 2026-09-15, after every model's release)

| Task | Source | n |
|---|---|---|
| T1 Bug report or feature request | GitHub issues: microsoft/vscode, kubernetes/kubernetes | 547 |
| T2 Will the PR be merged | GitHub PRs: microsoft/vscode, vercel/next.js, microsoft/TypeScript | 472 |
| T3 Firefox component (39) | Mozilla Bugzilla | 534 |
| T4 Firefox severity | Mozilla Bugzilla | 292 |
| T5 Advisory severity | GitHub Advisory Database (CC-BY-4.0) | 480 |
| T6 CVE weakness type (20 CWEs) | NVD CVE 2.0 feed 2026 (public domain), MITRE CWE list | 500 |

Item texts are quoted from those public sources for research purposes; each item links to its source.
Hacker News comments are referenced by link only (`v2/company/hn_mentions_labels.json`), not reproduced.

## Reproduce

```bash
gh auth login                                   # GitHub data
echo 'OPENROUTER_API_KEY=...' > .env            # OpenRouter key (not committed)
cd v2
python3 collect_v2.py && python3 collect_nvd.py # rebuild data (or use the frozen data/dataset.jsonl)
python3 run_v2.py                               # ~63k requests, ~$3
python3 score_v2.py && python3 total_score.py   # report_v2.md, total_score.md
```

Re-scoring only needs `v2/data/` and `v2/results/` (no API key): `cd v2 && python3 score_v2.py && python3 total_score.py`.
Python 3.9+, standard library only.

## v1 (pilot)

The repository root (`collect.py`, `run.py`, `score.py`, `results/`, `report.md`) is the earlier pilot:
4 tasks, one phrasing, no pre-registration. Its weaknesses (a PR-merge shortcut, keyword-matchable components,
a single phrasing) motivated v2. It is kept for transparency; v2 reuses some of its helpers.

## Licence

Code: MIT (see `LICENSE`). Data files keep the terms of their sources listed above.
