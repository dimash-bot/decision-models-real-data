"""Label each Hacker News mention: is it about the model, and is it positive / neutral / negative?

Labeller: anthropic/claude-haiku-5.5 via OpenRouter (not one of the compared models), temperature 0,
sees only the text and the model name. Output: hn_mentions_labelled.json
"""
import concurrent.futures as cf
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from run import api_key  # noqa: E402

LABELLER = "anthropic/claude-haiku-5.5"
NAMES = {"jev": "TypeSafe Jev (a decision model / decision API)",
         "liquid-d1": "Liquid AI d1 / d1.1 / d1-ultra (decision models)",
         "decider": "Perplexity Decider / pplx-decider (decision models)",
         "luna-decisions": "OpenAI GPT-6 Luna Decisions (Decisions API)",
         "drex": "Nace.AI Drex / Drex Max (decision models)"}
PROMPT = """You label developer discussion for a product comparison.
Product: {name}
Text from Hacker News:
<<<
{text}
>>>
Answer with JSON only: {{"about_product": true|false, "sentiment": "positive"|"neutral"|"negative"}}
- about_product: true only if the text clearly refers to this specific product (not a person or another thing with the same name).
- sentiment: the author's opinion of THIS product only. Neutral if they just mention or describe it."""


def label(key, k, m):
    body = {"model": LABELLER, "temperature": 0, "max_tokens": 200, "reasoning": {"enabled": False},
            "messages": [{"role": "user", "content": PROMPT.format(name=NAMES[k], text=m["text"])}]}
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    for _ in range(3):
        try:
            txt = json.load(urllib.request.urlopen(req, timeout=60))["choices"][0]["message"]["content"]
            j = json.loads(txt[txt.index("{"): txt.rindex("}") + 1])
            return {**m, "about_product": bool(j["about_product"]), "sentiment": j["sentiment"]}
        except Exception as e:
            err = str(e)
    return {**m, "about_product": None, "sentiment": None, "error": err}


def main():
    key = api_key()
    raw = json.load(open(os.path.join(HERE, "hn_mentions_raw.json")))
    out = {}
    with cf.ThreadPoolExecutor(8) as ex:
        for k, ms in raw.items():
            out[k] = list(ex.map(lambda m: label(key, k, m), ms))
    json.dump(out, open(os.path.join(HERE, "hn_mentions_labelled.json"), "w"), indent=1)  # local only (contains comment text)
    pub = {k: [{x: m.get(x) for x in ("id", "url", "type", "created", "about_product", "sentiment")} for m in ms] for k, ms in out.items()}
    json.dump(pub, open(os.path.join(HERE, "hn_mentions_labels.json"), "w"), indent=1)  # published
    for k, ms in out.items():
        rel = [m for m in ms if m["about_product"]]
        c = {s: sum(m["sentiment"] == s for m in rel) for s in ("positive", "neutral", "negative")}
        print(f"{k:15} raw={len(ms):4} relevant={len(rel):4} {c} errors={sum('error' in m for m in ms)}")


if __name__ == "__main__":
    main()
