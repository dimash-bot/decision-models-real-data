# Pricing, deals, openness and data policy — neutral sources only

Checked 2026-11-06. To keep this objective, the same two sources are used for every company, and
no company's own marketing, docs or blog posts are used (including Nace's):

- **OpenRouter** public data: `api/v1/models/<id>/endpoints` (price, discount, cache price, context,
  host) and each model page's `dataPolicy` record (training, prompt retention, zero-data-retention).
  Raw copy: `openrouter_endpoints.json`.
- **Hugging Face** model metadata and the licence files themselves. Raw copy: `huggingface.json`.

Prices are what you pay through OpenRouter, per 1M input tokens. Every model charges $0 for output.

## A. Pricing and deals (OpenRouter)

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

## B. Openness and data policy

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

## What this means for a developer
- **Cheapest:** Decider V1.2 ($0.019) and d1.1 ($0.020).
- **Most open:** Decider V1.2: weights published under Apache-2.0 with no revenue limits.
- **Most private by default (per OpenRouter):** Jev, Decider and Drex Max: no training, no prompt
  retention, zero-data-retention available. GPT-6 Luna keeps prompts and has no ZDR option on
  OpenRouter. Liquid's record on OpenRouter is self-contradictory; check before sending sensitive data.
- **Licence limits:** Drex Max's open weights need a commercial licence for any org with more than
  $1M revenue or funding; Liquid's open d1 models need one at $10M revenue; Perplexity's need none.
