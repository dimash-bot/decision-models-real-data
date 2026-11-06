# Decision models on real tech data — pre-registered method (v2)

Written **before** any v2 data was collected or any model was run. The SHA-256 of this file is
recorded in `PREREGISTRATION.txt` together with the time it was frozen. Any later change to the
method is listed under "Deviations" at the end of the report, never edited in silently.

**Disclosure.** The author works at Nace.AI, which makes Drex (one of the models tested).
To limit bias: the method, prompts, metrics and decision rules below are fixed before running;
all prompts, data, raw model outputs and code are published; Drex gets no special treatment
(same prompts, same items, called through OpenRouter like everyone else).

## 1. Question
On real, recent software-engineering decisions, which OpenRouter decision model is the most
accurate and has the most trustworthy probabilities — and are the differences real?

## 2. Models (all via OpenRouter `POST /api/alpha/decisions`, default provider routing)
typesafe/jev-1.14, typesafe/jev-1.13, perplexity/pplx-decider-v1.2, liquid/d1-ultra, liquid/d1.1,
openai/gpt-6-luna-decisions, nace-ai/drex-max.

## 3. Data — real decisions made by maintainers, created 2026-09-15 or later
All models were released 2026-09-18 … 2026-10-21, so items cannot be in their training data.

| ID | Task | Source | Type | Ground truth | Target n |
|---|---|---|---|---|---|
| T1 | Bug report or feature request? | GitHub issues: microsoft/vscode, kubernetes/kubernetes | yes/no | maintainer label (`bug`/`feature-request`, `kind/bug`/`kind/feature`) | 550, balanced |
| T2 | Will this PR be merged? | GitHub PRs: microsoft/vscode, vercel/next.js, microsoft/TypeScript (bots and drafts excluded; created ≤ 2026-10-29) | yes/no | merged vs closed-unmerged | 400, balanced |
| T3 | Which Firefox component owns this bug? | Bugzilla, product Firefox, ~38 components with ≥10 new bugs (excluding `General`, `Untriaged`) | choice (all components at once) | final triaged component | ≤15 per component (~500) |
| T4 | Firefox bug severity | Bugzilla, product Firefox | score S4<S3<S2<S1 | triaged severity | all S1/S2 + equal S3/S4, ~300 |
| T5 | Security advisory severity | GitHub reviewed security advisories published ≥ 2026-09-15 | score low<medium<high<critical | GitHub-reviewed severity | ~120 per level (~480) |

Inputs are what a triager sees at filing time: title + body/description. Removed: labels,
issue-template type markers, system-info blocks, images, CVSS vectors/scores and the
words "CVSS"/score numbers in advisories, the PR author's association with the repo.
Text is cut to 4,000 characters. Choice/score options use the **source's own official
descriptions** (Bugzilla component descriptions, Mozilla severity definitions, GitHub
advisory severity definitions) — not text written for this test.

## 4. Prompts
Each task has **three phrasings** of the question (P1 plain, P2 terse, P3 detailed), written
once and used for every model. A model's score on a task = mean over the three phrasings.
Phrasing sensitivity (spread across P1–P3) is reported per model.

## 5. Baselines (every model must beat these to count)
- **Prior**: always predict the class frequencies of that task (sets the floor for Brier).
- **Rule** (uses information the models do NOT get, to show what shortcuts exist):
  T2 author-association rule; T3 "component name appears in the title, else most common";
  T1 keyword rule (add/support/allow/option/feature request → feature).

## 6. Metrics
- **Primary (decides "best")**: balanced accuracy per task (= mean recall over classes), averaged
  over the five tasks with equal weight.
- **Secondary**: Brier score (multi-class, lower better), expected calibration error (10 bins),
  macro-F1, AUC (T1, T2), quadratic-weighted kappa and within-one-level accuracy (T4, T5),
  accuracy on the subset where the model is ≥90% confident and how large that subset is,
  refusal rate, p50/p95 latency, cost per 1,000 decisions (from OpenRouter's billed `usage.cost`).
- Refusals and unparseable answers count as wrong, with uniform probabilities. API transport
  errors are retried; items still failing for any model after retries are dropped for all models
  and the count is reported.

## 7. Statistics
- 95% intervals by **paired bootstrap over items** (2,000 resamples; for the overall score,
  resampled within each task).
- **Pairwise differences** in the primary metric for all 21 model pairs, paired bootstrap p-values,
  **Holm–Bonferroni** correction across the 21 pairs (per task and overall).
- **Rank uncertainty**: in each bootstrap resample, rank the models; report each model's
  probability of being ranked #1 and its 95% rank interval.
- **Decision rule**: a model is called "the best" only if it is #1 and its lead over #2 is
  significant after Holm correction (adjusted p < 0.05). Otherwise the report names the
  statistically tied top group.
- **Repeatability**: 100 items per task re-sent once with P1; report answer agreement and mean
  absolute change in probability.
- **Label noise**: T4 — share of bugs whose severity was changed after it was first set
  (Bugzilla history); all tasks — list of items where all seven models agree with each other
  but not with the label, published for human audit.

## 8. What this does NOT show
Only software-engineering text in English; no images; one hosting provider per model as routed
by OpenRouter (latency reflects the host as well as the model); prices as of the run date.

## Amendment 1 (2026-11-06, before any v2 model call)
At the author's request a ready-made public dataset was added: the **NVD CVE 2.0 JSON feed for 2026**
(`nvdcve-2.0-2026.json.gz`, SHA-256 verified against NVD's `.meta` file, stored in `data/raw/`).

| ID | Task | Source | Type | Ground truth | Target n |
|---|---|---|---|---|---|
| T6 | Which weakness type (CWE) is this vulnerability? | NVD feed, CVEs published ≥ 2026-09-15, not rejected, with exactly one CWE in the record | choice among the 20 most frequent CWEs | the CWE in the CVE record (assigned by the CNA or NVD) | ≤ 25 per CWE (~500) |

Input: the English CVE description only. Removed: `CWE-<n>` identifiers, CVSS vectors/scores.
Options use MITRE's official CWE names and descriptions (CWE list 1000, `cwec_latest.csv`).
T6 is added to every analysis in sections 6-7 exactly like T1-T5 (equal task weight, so the overall
score becomes the mean over six tasks). Known limitation: many descriptions name the weakness
(e.g. "cross-site scripting"), and CNA-assigned CWEs are not always analyst-reviewed.
