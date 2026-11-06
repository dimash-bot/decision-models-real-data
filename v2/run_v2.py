"""Send every v2 item x 3 phrasings to every model; then a repeat of P1 on 100 items/task.

Resumable: results/<model>.jsonl, one line per (item, variant); last line per key wins.
Usage:
  python3 run_v2.py --limit 2          # smoke test (2 items per task)
  python3 run_v2.py                    # full run, all models in parallel
  python3 run_v2.py --retry-errors
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

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from run import MODELS, api_key, slug  # noqa: E402  (v1 helpers: model list, key, file names)
from tasks_v2 import TASKS, VARIANTS, questions  # noqa: E402

URL = "https://openrouter.ai/api/alpha/decisions"
NACE_URL = "https://console.nace.ai/v1/systemone"


def nace_key():
    env = os.path.join(os.path.dirname(HERE), ".env")
    for line in open(env):
        if line.startswith("NACE_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    sys.exit("Add NACE_API_KEY=... to decision-eval/.env")
RESULTS = os.path.join(HERE, "results")
REPEAT_N = 100
print_lock = threading.Lock()


def log(*a):
    with print_lock:
        print(*a, file=sys.stderr, flush=True)


def call(key, model, question, state, tries=5, url=None):
    data = json.dumps({"model": model, "questions": {"q": question}, "state": state}).encode()
    headers = {"Authorization": "Bearer " + key, "Content-Type": "application/json",
               "HTTP-Referer": "https://nace.ai", "X-OpenRouter-Title": "decision-eval-v2"}
    last = None
    for i in range(tries):
        t0 = time.time()
        try:
            req = urllib.request.Request(url or URL, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=120) as r:
                resp = json.load(r)
            ans = (resp.get("answers") or {}).get("q")
            return {"answer": ans, "latency_ms": round((time.time() - t0) * 1000, 1), "usage": resp.get("usage"),
                    "provider": resp.get("provider"), "served_model": resp.get("model"),
                    "error": None if ans else "no answer in response"}
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:500]
            last = f"HTTP {e.code}: {msg}"
            if "refused to answer" in msg:
                return {"answer": {"type": "refusal", "detail": msg[:200]}, "latency_ms": round((time.time() - t0) * 1000, 1),
                        "usage": None, "provider": None, "served_model": None, "error": None}
            if e.code == 402:
                break  # out of credits: retrying won't help
            if e.code in (408, 429, 500, 502, 503, 524, 529) and i < tries - 1:
                time.sleep(2 ** i * 3 + random.random())
                continue
            break
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
            if i < tries - 1:
                time.sleep(2 ** i * 3)
                continue
    return {"answer": None, "latency_ms": None, "usage": None, "provider": None, "served_model": None, "error": last}


def jobs_for(items):
    """(item, variant) pairs: all items x P1-P3, plus 'R1' = repeat of P1 on the first REPEAT_N items per task."""
    jobs = [(it, v) for it in items for v in VARIANTS]
    seen = {}
    for it in items:
        seen.setdefault(it["task"], []).append(it)
    jobs += [(it, "R1") for t in seen for it in seen[t][:REPEAT_N]]
    return jobs


def run_model(model, items, key, conc, retry_errors, api_model=None, url=None):
    """model = label stored in results; api_model = name sent to the API (defaults to model)."""
    path = os.path.join(RESULTS, slug(model) + ".jsonl")
    done = {}
    if os.path.exists(path):
        for l in open(path):
            r = json.loads(l)
            done[(r["id"], r["variant"])] = r
    todo = [(it, v) for it, v in jobs_for(items)
            if (it["id"], v) not in done or (retry_errors and done[(it["id"], v)]["error"])]
    log(f"{model}: {len(todo)} to send")
    lock, n_err = threading.Lock(), 0

    def work(job):
        it, v = job
        q = questions(it["task"], "P1" if v == "R1" else v)
        return it, v, call(key, api_model or model, q, it["state"], url=url)

    with cf.ThreadPoolExecutor(conc) as ex, open(path, "a") as f:
        for n, (it, v, res) in enumerate(ex.map(work, todo), 1):
            with lock:
                f.write(json.dumps({"id": it["id"], "task": it["task"], "variant": v, "model": model, **res}) + "\n")
                f.flush()
            if res["error"]:
                n_err += 1
                if n_err <= 3:
                    log(f"  ! {model} {it['id']} {v}: {res['error'][:160]}")
            if n % 1000 == 0 or n == len(todo):
                log(f"  {model}: {n}/{len(todo)} errors={n_err}")
    return model, n_err


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=MODELS)
    ap.add_argument("--tasks", nargs="*", default=TASKS)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--concurrency", type=int, default=8, help="per model")
    ap.add_argument("--retry-errors", action="store_true")
    ap.add_argument("--nace", metavar="API_MODEL", help="call Nace's own API with this model name (e.g. drex-max-v1.1); "
                    "results are stored under the label given by --models")
    a = ap.parse_args()
    key, url = api_key(), None
    if a.nace:
        key, url = nace_key(), NACE_URL
    items = [json.loads(l) for l in open(os.path.join(HERE, "data", "dataset.jsonl"))]
    items = [i for i in items if i["task"] in a.tasks]
    if a.limit:
        per, kept = {}, []
        for i in items:
            per[i["task"]] = per.get(i["task"], 0) + 1
            if per[i["task"]] <= a.limit:
                kept.append(i)
        items = kept
    os.makedirs(RESULTS, exist_ok=True)
    with cf.ThreadPoolExecutor(len(a.models)) as ex:
        for model, n_err in ex.map(lambda m: run_model(m, items, key, a.concurrency, a.retry_errors, a.nace, url), a.models):
            log(f"done {model}: errors={n_err}")


if __name__ == "__main__":
    main()
