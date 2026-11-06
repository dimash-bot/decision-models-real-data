"""Score results/*.jsonl against data/dataset.jsonl and write report.md + summary.csv.

Usage: python3 score.py [--baseline nace-ai/drex-max]
"""
import argparse
import csv
import glob
import json
import math
import os
import random
import re
from collections import defaultdict

from tasks import FF_COMPONENTS, FF_SEVERITY, SEV_INDEX

HERE = os.path.dirname(os.path.abspath(__file__))
EPS = 1e-6
CONF = 0.9  # "confident" threshold
BOOT = 1000
TASK_NAMES = {
    "issue_type": "A. VS Code issue: bug vs feature",
    "pr_merged": "B. PR will be merged",
    "ff_component": "C. Firefox bug -> component (8)",
    "ff_severity": "D. Firefox bug severity (S1-S4)",
}
COMPONENTS = list(FF_COMPONENTS)


# --------------------------------------------------------------------------- parsing
def level_of(key):
    """Map a score-probability key to a severity index 0..3 (S4..S1)."""
    k = str(key).strip()
    m = re.match(r"^S([1-4])\b", k)
    if m:
        return SEV_INDEX["S" + m.group(1)]
    for i, c in enumerate(FF_SEVERITY):
        if k == c:
            return i
    if re.fullmatch(r"-?\d+(\.0+)?", k):
        v = int(float(k))
        if 0 <= v < len(FF_SEVERITY):
            return v
        if 1 <= v <= len(FF_SEVERITY):
            return v - 1
    return None


def normalize(p):
    s = sum(p)
    return [x / s for x in p] if s > 0 else [1 / len(p)] * len(p)


def predict(task, ans):
    """Return a probability vector over the task's classes (None = refusal / unusable)."""
    if not ans or ans.get("type") == "refusal":
        return None
    if task in ("issue_type", "pr_merged"):
        if "noul" not in ans:
            return None
        p = min(max(float(ans["noul"]), 0.0), 1.0)
        return [1 - p, p]  # [false, true]
    if task == "ff_component":
        probs = ans.get("probabilities") or {}
        v = [float(probs.get(c, 0.0)) for c in COMPONENTS]
        if sum(v) == 0 and ans.get("choice") in COMPONENTS:
            v[COMPONENTS.index(ans["choice"])] = 1.0
        return normalize(v) if sum(v) > 0 else None
    if task == "ff_severity":
        n = len(FF_SEVERITY)
        v = [0.0] * n
        for k, p in (ans.get("probabilities") or {}).items():
            i = level_of(k)
            if i is not None:
                v[i] += float(p)
        if sum(v) == 0 and "score" in ans:
            s = float(ans["score"])
            idx = round(s * (n - 1)) if 0 <= s <= 1 and not float(s).is_integer() else level_of(s)
            if idx is not None:
                v[int(idx)] = 1.0
        return normalize(v) if sum(v) > 0 else None


def truth_index(task, t):
    if task in ("issue_type", "pr_merged"):
        return 1 if t else 0
    if task == "ff_component":
        return COMPONENTS.index(t)
    return SEV_INDEX[t]


# --------------------------------------------------------------------------- metrics
def argmax(v):
    return max(range(len(v)), key=lambda i: v[i])


def auc(scores, labels):
    pos = [s for s, l in zip(scores, labels) if l]
    neg = [s for s, l in zip(scores, labels) if not l]
    if not pos or not neg:
        return float("nan")
    ranked = sorted((s, i) for i, s in enumerate(scores))
    ranks = [0.0] * len(scores)
    i = 0
    while i < len(ranked):
        j = i
        while j + 1 < len(ranked) and ranked[j + 1][0] == ranked[i][0]:
            j += 1
        for k in range(i, j + 1):
            ranks[ranked[k][1]] = (i + j) / 2 + 1
        i = j + 1
    rp = sum(r for r, l in zip(ranks, labels) if l)
    return (rp - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def spearman(x, y):
    def rank(a):
        o = sorted(range(len(a)), key=lambda i: a[i])
        r = [0.0] * len(a)
        i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and a[o[j + 1]] == a[o[i]]:
                j += 1
            for k in range(i, j + 1):
                r[o[k]] = (i + j) / 2
            i = j + 1
        return r
    rx, ry = rank(x), rank(y)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    vx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    vy = math.sqrt(sum((b - my) ** 2 for b in ry))
    return cov / (vx * vy) if vx and vy else float("nan")


def macro_f1(pred, true, k):
    f = []
    for c in range(k):
        tp = sum(p == c and t == c for p, t in zip(pred, true))
        fp = sum(p == c and t != c for p, t in zip(pred, true))
        fn = sum(p != c and t == c for p, t in zip(pred, true))
        if tp + fp + fn == 0:
            continue
        f.append(2 * tp / (2 * tp + fp + fn))
    return sum(f) / len(f) if f else float("nan")


def ece(conf, correct, bins=10):
    tot, n = 0.0, len(conf)
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        idx = [i for i, c in enumerate(conf) if (lo < c <= hi) or (b == 0 and c == lo)]
        if idx:
            acc = sum(correct[i] for i in idx) / len(idx)
            avg = sum(conf[i] for i in idx) / len(idx)
            tot += len(idx) / n * abs(acc - avg)
    return tot


def task_metrics(task, rows):
    """rows: list of (prob_vector or None, truth_idx). Refusals count as wrong, uniform probs."""
    k = 2 if task in ("issue_type", "pr_merged") else len(COMPONENTS) if task == "ff_component" else len(FF_SEVERITY)
    P = [p if p is not None else [1 / k] * k for p, _ in rows]
    T = [t for _, t in rows]
    pred = [argmax(p) if r[0] is not None else -1 for p, r in zip(P, rows)]
    correct = [int(a == b) for a, b in zip(pred, T)]
    conf = [max(p) for p in P]
    brier = sum(sum((p[c] - (c == t)) ** 2 for c in range(k)) for p, t in zip(P, T)) / len(T)
    logloss = -sum(math.log(max(p[t], EPS)) for p, t in zip(P, T)) / len(T)
    hi = [c for c, cf in zip(correct, conf) if cf >= CONF]
    m = {
        "n": len(T),
        "refusals": sum(r[0] is None for r in rows),
        "accuracy": sum(correct) / len(T),
        "macro_f1": macro_f1(pred, T, k),
        "brier": brier,
        "log_loss": logloss,
        "ece": ece(conf, correct),
        "conf90_coverage": len(hi) / len(T),
        "conf90_accuracy": sum(hi) / len(hi) if hi else float("nan"),
        "_correct": correct,
    }
    if k == 2:
        m["auc"] = auc([p[1] for p in P], T)
    if task == "ff_severity":
        exp = [sum(i * x for i, x in enumerate(p)) for p in P]
        m["mae"] = sum(abs(a - b) for a, b in zip(pred, T) if a >= 0) / max(1, sum(a >= 0 for a in pred))
        m["within_1"] = sum(abs(a - b) <= 1 for a, b in zip(pred, T) if a >= 0) / len(T)
        m["spearman"] = spearman(exp, T)
    return m


def bootstrap_ci(correct, seed=0):
    rng = random.Random(seed)
    n = len(correct)
    stats = sorted(sum(correct[rng.randrange(n)] for _ in range(n)) / n for _ in range(BOOT))
    return stats[int(0.025 * BOOT)], stats[int(0.975 * BOOT) - 1]


def mcnemar_p(a, b):
    """Exact two-sided McNemar test on paired correctness lists."""
    n01 = sum(x == 1 and y == 0 for x, y in zip(a, b))
    n10 = sum(x == 0 and y == 1 for x, y in zip(a, b))
    n = n01 + n10
    if n == 0:
        return 1.0
    k = min(n01, n10)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def pct(x, d=1):
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{100 * x:.{d}f}%"


def num(x, d=3):
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{d}f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", default="nace-ai/drex-max")
    ap.add_argument("--exclude", nargs="*", default=[], help="models to leave out (e.g. an unfinished run)")
    a = ap.parse_args()

    items = {json.loads(l)["id"]: json.loads(l) for l in open(os.path.join(HERE, "data", "dataset.jsonl"))}
    results = {}
    for path in sorted(glob.glob(os.path.join(HERE, "results", "*.jsonl"))):
        recs = {}
        for l in open(path):
            r = json.loads(l)
            recs[r["id"]] = r
        for r in recs.values():  # a model refusing is an answer (counts as wrong), not an API failure
            if r["error"] and "refused to answer" in r["error"]:
                r["answer"], r["error"] = {"type": "refusal"}, None
        if recs and next(iter(recs.values()))["model"] not in a.exclude:
            results[next(iter(recs.values()))["model"]] = recs
    if not results:
        raise SystemExit("no results yet - run run.py first")

    # only score items every model answered without an API error (paired comparison)
    ids = [i for i in items if all(i in r and not r[i]["error"] for r in results.values())]
    tasks = [t for t in TASK_NAMES if any(items[i]["task"] == t for i in ids)]

    M, ops = {}, {}
    for model, recs in results.items():
        allr = list(recs.values())
        lat = sorted(r["latency_ms"] for r in allr if r["latency_ms"])
        cost = [r["usage"]["cost"] for r in allr if r.get("usage") and r["usage"].get("cost") is not None]
        tok = [r["usage"]["input_tokens"] for r in allr if r.get("usage") and r["usage"].get("input_tokens")]
        ops[model] = {
            "sent": len(allr),
            "api_errors": sum(bool(r["error"]) for r in allr),
            "p50_ms": lat[len(lat) // 2] if lat else None,
            "p95_ms": lat[int(len(lat) * 0.95)] if lat else None,
            "cost_per_1k": 1000 * sum(cost) / len(cost) if cost else None,
            "avg_input_tokens": sum(tok) / len(tok) if tok else None,
            "providers": sorted({r["provider"] for r in allr if r.get("provider")}),
        }
        for t in tasks:
            rows = [(predict(t, recs[i]["answer"]), truth_index(t, items[i]["truth"])) for i in ids if items[i]["task"] == t]
            m = task_metrics(t, rows)
            m["ci"] = bootstrap_ci(m["_correct"])
            M[(model, t)] = m

    models = sorted(results, key=lambda m: -sum(M[(m, t)]["accuracy"] for t in tasks) / len(tasks))
    base = a.baseline if a.baseline in results else None

    L = ["# Decision model comparison on real data", ""]
    L.append(f"Items scored: {len(ids)} (only items every model answered without an API error; "
             f"refusals count as wrong). Data created after 2026-09-15; ground truth = maintainers' real decisions.")
    L.append("")
    L.append("## Overall (mean over tasks)")
    L.append("")
    L.append("| Model | Mean accuracy | Mean Brier (lower better) | Mean ECE (lower better) | p50 latency | p95 latency | Cost / 1k decisions | API errors |")
    L.append("|---|---|---|---|---|---|---|---|")
    for m in models:
        acc = sum(M[(m, t)]["accuracy"] for t in tasks) / len(tasks)
        br = sum(M[(m, t)]["brier"] for t in tasks) / len(tasks)
        ec = sum(M[(m, t)]["ece"] for t in tasks) / len(tasks)
        o = ops[m]
        L.append(f"| {m} | {pct(acc)} | {num(br)} | {num(ec)} | {num(o['p50_ms'], 0)} ms | {num(o['p95_ms'], 0)} ms | "
                 f"{'$' + num(o['cost_per_1k'], 4) if o['cost_per_1k'] is not None else '-'} | {o['api_errors']}/{o['sent']} |")
    for t in tasks:
        L += ["", f"## {TASK_NAMES[t]}", ""]
        extra = ["AUC"] if t in ("issue_type", "pr_merged") else ["MAE", "Within 1", "Spearman"] if t == "ff_severity" else []
        hdr = ["Model", "Accuracy (95% CI)", "Macro-F1", *extra, "Brier", "Log loss", "ECE", "Acc. when >=90% sure", "Share >=90% sure", "Refusals"]
        if base:
            hdr.append(f"vs {base.split('/')[-1]} (p)")
        L.append("| " + " | ".join(hdr) + " |")
        L.append("|" + "---|" * len(hdr))
        for m in models:
            x = M[(m, t)]
            row = [m, f"{pct(x['accuracy'])} ({pct(x['ci'][0], 0)}-{pct(x['ci'][1], 0)})", num(x["macro_f1"])]
            if t in ("issue_type", "pr_merged"):
                row.append(num(x["auc"]))
            if t == "ff_severity":
                row += [num(x["mae"], 2), pct(x["within_1"]), num(x["spearman"])]
            row += [num(x["brier"]), num(x["log_loss"]), num(x["ece"]), pct(x["conf90_accuracy"]), pct(x["conf90_coverage"]), str(x["refusals"])]
            if base:
                row.append("-" if m == base else num(mcnemar_p(M[(m, t)]["_correct"], M[(base, t)]["_correct"]), 3))
            L.append("| " + " | ".join(row) + " |")
        L.append(f"\nn = {M[(models[0], t)]['n']}")
    L += ["", "## How to read this", "",
          "- **Brier / log loss / ECE**: quality of the probabilities. Lower is better. ECE = gap between stated confidence and actual accuracy.",
          "- **Acc. when >=90% sure**: how often the model is right when it says it is at least 90% sure; *Share* = how often it says that.",
          f"- **p** column: exact McNemar test of each model's per-item correctness against {base or 'the baseline'}; p < 0.05 = the accuracy gap is unlikely to be chance.",
          "- Providers: " + "; ".join(f"{m}: {', '.join(ops[m]['providers']) or '-'}" for m in models)]
    open(os.path.join(HERE, "report.md"), "w").write("\n".join(L) + "\n")

    with open(os.path.join(HERE, "summary.csv"), "w", newline="") as f:
        w = csv.writer(f)
        keys = ["n", "refusals", "accuracy", "macro_f1", "auc", "mae", "within_1", "spearman", "brier", "log_loss", "ece", "conf90_accuracy", "conf90_coverage"]
        w.writerow(["model", "task", *keys, "ci_low", "ci_high"])
        for m in models:
            for t in tasks:
                x = M[(m, t)]
                w.writerow([m, t, *[x.get(k, "") for k in keys], *x["ci"]])
    print("\n".join(L))


if __name__ == "__main__":
    main()
