# Total score — pre-registered formula (frozen before the v2 run)

Five pillars, each scored 0-100 with fixed, absolute rules (no "best model = 100" rescaling of
small differences, except where noted). Weights are fixed here; section 7 shows how the ranking
changes under other weightings, so readers can see whether the winner depends on the weights.

| Pillar | Weight | What it measures |
|---|---|---|
| Quality | 45% | How often the model makes the right call on real tech decisions |
| Efficiency | 20% | What it costs and how fast it answers |
| Trust | 20% | What happens to your data, how open the model is, how reliable the API is |
| Reviews | 10% | What developers do (usage) and say (discussion) |
| Signup bonus | 5% | Free credit a new developer gets |

## 1. Quality (45%)
From the pre-registered evaluation (METHODOLOGY.md): mean over the five tasks of
`skill = (balanced accuracy - chance) / (1 - chance) x 100`, where chance = 1 / number of classes.
So 0 = no better than guessing, 100 = always right. Calibration enters as a penalty:
`quality = 0.8 x skill + 0.2 x (1 - mean Brier / prior Brier) x 100` (prior Brier = always predicting
the class frequencies). Uncertainty: computed in every bootstrap resample of the evaluation.

## 2. Efficiency (20%)
- **Cost (12 of 20)**: billed `usage.cost` per 1,000 decisions in our run, at the price on the run
  date. `score = 100 x log10(0.5 / cost) / log10(0.5 / 0.005)`, clipped to 0-100
  (i.e. $0.005 per 1k decisions = 100, $0.50 per 1k = 0; log scale, so halving cost always gains the
  same points). Drex Max is currently on a 50%-off promotion; the report also shows its score at list price.
- **Speed (8 of 20)**: median latency in our run. `score = 100 x log10(5000 / p50_ms) / log10(5000 / 100)`,
  clipped (100 ms = 100, 5 s = 0).

## 3. Trust (20%) — checklist, sources: OpenRouter model records, Hugging Face, our own run
| Item | Points |
|---|---|
| Does not train on prompts (OpenRouter `dataPolicy.training = false`) | 20 |
| Does not retain prompts (`retainsPrompts = false`) | 15 |
| Zero-data-retention available on OpenRouter | 10 |
| Weights of the served model published | 15 |
| Licence: permissive (Apache/MIT) 10; restricted-commercial 5; none/closed 0 | 10 |
| Base model / size disclosed for the served model | 10 |
| Reliability in our run: share of requests answered without API error or refusal (`10 x (rate - 0.95)/0.05`, clipped 0-10) | 10 |
| Consistency in our run: same answer when the identical request is repeated (`10 x (rate - 0.90)/0.10`, clipped 0-10) | 10 |
Conflicting OpenRouter records (e.g. one says training yes, another no) score half points.

## 4. Reviews (10%)
- **Usage (6 of 10)**: OpenRouter decision requests in the latest week (rankings page).
  `score = 100 x log10(requests / 1e6) / log10(1e10 / 1e6)`, clipped (1M/week = 0, 10B/week = 100).
- **Discussion (4 of 10)**: Hacker News stories/comments since 2026-09-01 that clearly refer to the
  model (exact-name queries, then each hit checked to be about that model). Each is labelled
  positive / neutral / negative by a model that is **not** part of the comparison, given only the text.
  `score = 50 + 50 x (pos - neg) / n`. If fewer than 10 relevant mentions: score = 50 (neutral) and
  marked "insufficient data".

## 5. Signup bonus (5%)
Free credit for a new account on the provider's own API, from the provider's official pricing page
(the one place this is published; the same page type is used for every provider). Converted to
"free decisions" at that provider's own price for a 1,200-token request.
`score = 100 x log10(1 + free_decisions) / log10(1 + 1,000,000)`, clipped. None = 0.
Note: these bonuses do not apply when you use the models through OpenRouter.

## 6. Total
`total = 0.45 Q + 0.20 E + 0.20 T + 0.10 R + 0.05 B`. Reported with a 95% interval from the
quality bootstrap (other pillars are fixed facts on the run date).

## 7. Is the winner just the weights? (sensitivity)
Reported alongside the main ranking:
1. Quality only; 2. equal weights (20% each); 3. no signup bonus; 4. Drex Max at list price;
5. **10,000 random weightings** (uniform over all weight combinations): share of weightings in
which each model ranks #1.
A model is called "best overall" only if it is #1 under the main weights **and** wins in more than
50% of random weightings. Otherwise the report says the result depends on what you value.

**Disclosure.** The author works at Nace.AI (Drex). This formula was fixed before any v2 results
existed and is published with all inputs.
