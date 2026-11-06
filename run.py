"""Send every dataset item to every model through OpenRouter's Decisions API.

Resumable: results/<model>.jsonl keeps one line per item; finished items are skipped.

Usage:
  export OPENROUTER_API_KEY=...        (or put OPENROUTER_API_KEY=... in decision-eval/.env)
  python3 run.py                       # all models, all items
  python3 run.py --limit 5             # smoke test: 5 items per task
  python3 run.py --models nace-ai/drex-max --tasks ff_severity
  python3 run.py --retry-errors        # re-send items that failed last time
"""
import argparse
import concurrent.futures as cf
import json
import os
import random
import sys
import threading
import time
import urllib.error
import urllib.request

from tasks import QUESTIONS

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "dataset.jsonl")
RESULTS = os.path.join(HERE, "results")
URL = "https://openrouter.ai/api/alpha/decisions"
MODELS = [
    "typesafe/jev-1.14",
    "typesafe/jev-1.13",
    "perplexity/pplx-decider-v1.2",
    "liquid/d1-ultra",
    "liquid/d1.1",
    "openai/gpt-6-luna-decisions",
    "nace-ai/drex-max",
]


def api_key():
    k = os.environ.get("OPENROUTER_API_KEY")
    env = os.path.join(HERE, ".env")
    if not k and os.path.exists(env):
        for line in open(env):
            if line.startswith("OPENROUTER_API_KEY="):
                k = line.split("=", 1)[1].strip().strip('"')
    if not k:
        sys.exit("Set OPENROUTER_API_KEY (env var or decision-eval/.env)")
    return k


def slug(model):
    return model.replace("/", "__")


def call(key, model, item, tries=4):
    body = {"model": model, "questions": {"q": QUESTIONS[item["task"]]}, "state": item["state"]}
    data = json.dumps(body).encode()
    headers = {
        "Authorization": "Bearer " + key,
        "Content-Type": "application/json",
        "HTTP-Referer": "https://nace.ai",
        "X-OpenRouter-Title": "decision-eval",
    }
    last = None
    for i in range(tries):
        t0 = time.time()
        try:
            req = urllib.request.Request(URL, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=120) as r:
                resp = json.load(r)
            ms = (time.time() - t0) * 1000
            ans = (resp.get("answers") or {}).get("q")
            return {
                "answer": ans,
                "latency_ms": round(ms, 1),
                "usage": resp.get("usage"),
                "provider": resp.get("provider"),
                "served_model": resp.get("model"),
                "error": None if ans else "no answer in response",
            }
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:500]
            last = f"HTTP {e.code}: {msg}"
            if "refused to answer" in msg:  # the model declined: that is its answer, not a transport error
                return {"answer": {"type": "refusal", "detail": msg[:200]}, "latency_ms": round((time.time() - t0) * 1000, 1),
                        "usage": None, "provider": None, "served_model": None, "error": None}
            if e.code in (408, 429, 500, 502, 503, 524, 529) and i < tries - 1:
                time.sleep(2 ** i * 3 + random.random())
                continue
            break
        except Exception as e:  # timeouts, connection resets
            last = f"{type(e).__name__}: {e}"
            if i < tries - 1:
                time.sleep(2 ** i * 3)
                continue
    return {"answer": None, "latency_ms": None, "usage": None, "provider": None, "served_model": None, "error": last}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=MODELS)
    ap.add_argument("--tasks", nargs="*", default=list(QUESTIONS))
    ap.add_argument("--limit", type=int, default=0, help="items per task (0 = all)")
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--retry-errors", action="store_true")
    a = ap.parse_args()

    key = api_key()
    items = [json.loads(l) for l in open(DATA)]
    items = [i for i in items if i["task"] in a.tasks]
    if a.limit:
        seen = {}
        items = [i for i in items if seen.setdefault(i["task"], []).append(1) or len(seen[i["task"]]) <= a.limit]
    os.makedirs(RESULTS, exist_ok=True)

    for model in a.models:
        path = os.path.join(RESULTS, slug(model) + ".jsonl")
        done = {}
        if os.path.exists(path):
            for l in open(path):
                r = json.loads(l)
                done[r["id"]] = r
        todo = [i for i in items if i["id"] not in done or (a.retry_errors and done[i["id"]]["error"])]
        print(f"{model}: {len(todo)} to send ({len(items) - len(todo)} already done)", file=sys.stderr)
        if not todo:
            continue
        lock = threading.Lock()
        n_err = 0

        def work(item):
            return item, call(key, model, item)

        with cf.ThreadPoolExecutor(a.concurrency) as ex, open(path, "a") as f:
            for n, (item, res) in enumerate(ex.map(work, todo), 1):
                rec = {"id": item["id"], "task": item["task"], "model": model, **res}
                with lock:  # append as we go; later lines for an id win on reload
                    f.write(json.dumps(rec) + "\n")
                    f.flush()
                n_err += bool(res["error"])
                if n % 50 == 0 or n == len(todo):
                    print(f"  {n}/{len(todo)}  errors={n_err}", file=sys.stderr)
                if res["error"] and n_err <= 3:
                    print(f"  ! {item['id']}: {res['error'][:200]}", file=sys.stderr)


if __name__ == "__main__":
    main()
