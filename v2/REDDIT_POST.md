**Title:** I tested 7 "decision models" on OpenRouter against 2,800 real GitHub, Firefox and CVE decisions. Three are statistically tied for best; GPT-6 Luna came last.

---

**Disclosure first:** I work at Nace.AI, which makes Drex Max, one of the models tested. To keep that from tilting anything, the method, prompts and scoring formula were written down and checksummed **before** any model was run; every model got identical inputs through OpenRouter; and all data, raw model outputs and code are published so you can re-score it yourself. Pricing and openness come from OpenRouter, Hugging Face and each provider's own price list, never from any company's marketing claims (Nace's included).

## What I tested

Decision models don't write text: you give them some input and a typed question (yes/no, pick one, or a score) and they return a probability for every option. Models: **TypeSafe Jev 1.14 and 1.13, Perplexity Decider V1.2, Liquid d1-ultra and d1.1, OpenAI GPT-6 Luna Decisions, Nace Drex Max.**

**Data:** real decisions made by real maintainers, all created **after Sep 15, 2026**, i.e. after every model was released, so none of it can be in their training data:

| Task | Source | n | Question |
|---|---|---|---|
| T1 | VS Code + Kubernetes issues | 547 | Bug report or feature request? |
| T2 | VS Code, Next.js, TypeScript PRs | 472 | Will it be merged? |
| T3 | Firefox bugs (Bugzilla) | 534 | Which of 39 components? |
| T4 | Firefox bugs | 292 | Severity S4-S1? |
| T5 | GitHub security advisories | 480 | Severity low-critical? |
| T6 | NVD CVE feed (ready-made public dataset) | 500 | Which of 20 weakness types (CWE)? |

Labels, template markers, CVSS scores and CWE numbers were stripped from the inputs. Each question was asked in **3 different phrasings** and averaged, so no model wins because of my wording. Classes are balanced, the score is **balanced accuracy**, and all comparisons use paired bootstrap confidence intervals with Holm correction. About 63,000 API calls in total; it cost $3.

## Results: accuracy

| Model | Balanced accuracy (95% CI) | Chance of being #1 | Cost per 1k decisions | Median / p95 latency |
|---|---|---|---|---|
| Liquid d1-ultra | **66.1%** (64.6-67.6) | 81% | $0.034 | 682 ms / **5.1 s** |
| Perplexity Decider V1.2 | **65.6%** (64.2-67.0) | 18% | **$0.018** | 784 ms / 1.3 s |
| Nace Drex Max | **64.9%** (63.5-66.3) | 1% | $0.055 | 731 ms / 1.2 s |
| TypeSafe Jev 1.13 | 64.2% (62.7-65.7) | 0% | $0.051 | 699 ms / 0.9 s |
| TypeSafe Jev 1.14 | 64.2% (62.6-65.7) | 0% | $0.051 | 678 ms / 0.8 s |
| Liquid d1.1 | 63.7% (62.3-65.1) | 0% | **$0.016** | **632 ms** / 0.7 s |
| GPT-6 Luna Decisions | 62.8% (61.5-64.2) | 0% | $0.091 | 758 ms / 1.1 s |

- **No single winner on accuracy.** d1-ultra, Decider and Drex Max are statistically tied (pre-registered rule: #1 must beat #2 after correction; it doesn't).
- **Significant gaps:** d1-ultra, Decider and Drex Max all beat GPT-6 Luna; d1-ultra also beats Jev 1.13/1.14 and d1.1.
- **Per task:** everyone is ~90-92% on bug-vs-feature. Decider leads Firefox components (77.6%) and CWE typing (76.0%); d1-ultra leads PR merging (63.6%) and advisory severity (45.1%); Jev 1.14 leads Firefox severity (47.1%), though all 7 are tied there.

## Other things worth knowing

- **A one-line rule beats every model at predicting PR merges.** "Was it opened by someone already involved in the repo?" gets 73% balanced accuracy; the best model gets 64%. The models don't get that field, but it shows how much of that decision isn't in the text.
- **Overconfidence:** GPT-6 Luna claims to be at least 90% sure on 61% of severity questions and is right only 40-52% of the time when it does. Drex Max is overconfident on PR merges: at least 90% sure 62% of the time, right 67% of those times. d1-ultra and Decider have the best-calibrated probabilities overall.
- **Reliability:** d1-ultra's provider timed out on about 1.8% of first attempts, and its p95 latency was 5.1 s. Retries recovered all but one request. Every other model had zero errors.
- **Consistency:** asked the identical question twice, Luna gave the same answer 100% of the time, Decider 99.3% and Jev 1.14 99.2%. d1.1 gave the same answer only 90.7% of the time.

## Total score (quality, efficiency, trust, reviews, signup bonus)

The weights were fixed in advance: quality 45%, efficiency 20%, trust 20%, reviews 10%, signup bonus 5%.
- **Trust:** whether the provider trains on or keeps your prompts and offers zero data retention (from OpenRouter's records), whether the weights and licence are published, and reliability and consistency in this run.
- **Reviews:** OpenRouter usage plus Hacker News sentiment, labelled by a model that isn't in the comparison.

| Model | Total | Quality | Efficiency | Trust | Reviews | Bonus |
|---|---|---|---|---|---|---|
| Perplexity Decider V1.2 | **59.2** | 47.8 | 62.1 | **99.3** | 53.9 | 0 |
| Nace Drex Max | 54.9 | 46.6 | 48.4 | 79.8 | 40.0 | **85.7** |
| Liquid d1-ultra | 49.7 | **49.2** | 55.6 | 43.1 | 40.2 | 76.6 |
| TypeSafe Jev 1.13 | 49.4 | 44.8 | 49.7 | 62.3 | **68.1** | 0 |
| TypeSafe Jev 1.14 | 49.3 | 44.8 | 50.0 | 64.2 | 63.1 | 0 |
| Liquid d1.1 | 49.1 | 44.7 | **66.0** | 38.2 | 39.9 | 82.0 |
| GPT-6 Luna Decisions | 39.1 | 41.0 | 41.4 | 39.9 | 43.7 | 0 |

**Read this before quoting the total score.**
- Decider is #1 under the pre-set weights. Under 10,000 random weightings it's #1 only 33% of the time, against Drex Max's 47%, so by the rule I fixed in advance, **no model is best overall.**
- **Drex Max's 47% comes entirely from its $5 signup bonus.** Drop the bonus pillar and Decider is #1 in **87%** of random weightings, Jev 1.13 in 12%, and Drex Max in 0%. The bonuses also don't apply if you use the models through OpenRouter.
- **Where you buy Drex Max matters.** It's the only model whose own API is cheaper than OpenRouter: **$0.03 per 1M input tokens on Nace's API** versus $0.06 on OpenRouter, where the $0.06 is a 50%-off promotion on a $0.12 list price. Direct, it would cost about $0.027 per 1k decisions (about 1.4x Decider instead of 3x), and its total score would rise from 54.9 to 56.7, still #2. Without the bonus pillar Decider still wins 86% of weightings. I only tested through OpenRouter, so the direct figure assumes Nace serves the same model.

**So if you're choosing:**
- **Best all-round value:** Perplexity Decider V1.2. It's tied for the most accurate, the second cheapest, and the most open: Apache-2.0 weights, no training on or retention of prompts per OpenRouter.
- **Highest accuracy:** Liquid d1-ultra, but expect latency spikes, and OpenRouter's records on Liquid's data policy contradict each other.
- **Cheapest:** Liquid d1.1, if you can accept slightly lower accuracy and less consistent answers.
- **Avoid for now:** GPT-6 Luna Decisions. It's the least accurate, the most expensive, the most overconfident, and keeps prompts with no zero-data-retention option on OpenRouter.

## Limitations
- English, software engineering only, text only (no images).
- Labels are human decisions and contain mistakes. On 381 items all 7 models agree with each other but not with the label; they're listed for anyone to audit.
- Many CVE descriptions name their weakness ("cross-site scripting"), which makes parts of T6 easy.
- Prices, uptime and usage are a snapshot from Nov 6, 2026.
- The reviews pillar is thin: only Jev and Luna had 10 or more relevant Hacker News mentions. The others got a neutral score.
- Openness, an observation rather than a conclusion: Hugging Face lists the same parameter count (26,085,330,160) for Drex Max and Perplexity Decider, which names Qwen3.8-27B as its base. Drex Max's model card names no base model.

Code, data, raw outputs, pre-registration and checksums: https://github.com/dimash-bot/decision-models-real-data
