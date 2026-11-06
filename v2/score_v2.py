"""Score v2 exactly as pre-registered in METHODOLOGY.md. Writes results.json, report_v2.md, label_audit.csv.

Usage: python3 score_v2.py [--boot 2000]
"""
import argparse
import csv
import json
import math
import os
import random
import re
from collections import Counter, defaultdict
from itertools import combinations

from tasks_v2 import ADV_LABELS, FF_SEV_LABELS, TASKS, VARIANTS, components, cwes

HERE = os.path.dirname(os.path.abspath(__file__))
EPS = 1e-6
TASK_NAMES = {
    "T1": "Bug report or feature request (GitHub issues)",
    "T2": "Will this PR be merged (GitHub PRs)",
    "T3": "Firefox bug -> component (all components)",
    "T4": "Firefox bug severity (S4-S1)",
    "T5": "Security advisory severity (low-critical)",
    "T6": "CVE weakness type (20 CWEs, NVD feed)",
}
CHOICE = {"T3": lambda: sorted(components()), "T6": lambda: sorted(cwes())}


# --------------------------------------------------------------------------- classes & parsing
def classes(task):
    if task in ("T1", "T2"):
        return [False, True]
    if task in CHOICE:
        return CHOICE[task]()
    return FF_SEV_LABELS if task == "T4" else ADV_LABELS


def probs(task, ans, k):
    """Probability vector over the task's classes, or None for refusal / unusable answer."""
    if not ans or ans.get("type") == "refusal":
        return None
    if task in ("T1", "T2"):
        if "noul" not in ans:
            return None
        p = min(max(float(ans["noul"]), 0.0), 1.0)
        return [1 - p, p]
    if task in CHOICE:
        cl = classes(task)
        pr = ans.get("probabilities") or {}
        v = [float(pr.get(c, 0.0)) for c in cl]
        if sum(v) == 0 and ans.get("choice") in cl:
            v[cl.index(ans["choice"])] = 1.0
    else:
        v = [0.0] * k
        for key, p in (ans.get("probabilities") or {}).items():
            if re.fullmatch(r"\d+", str(key)) and int(key) < k:
                v[int(key)] += float(p)
        if sum(v) == 0 and "score" in ans:  # fall back to the scalar score in [0,1]
            v[min(k - 1, max(0, round(float(ans["score"]) * (k - 1))))] = 1.0
    s = sum(v)
    return [x / s for x in v] if s > 0 else None


def argmax(v):
    return max(range(len(v)), key=v.__getitem__)


# --------------------------------------------------------------------------- metrics
def balanced_acc(pred, truth, k):
    per = defaultdict(list)
    for p, t in zip(pred, truth):
        per[t].append(p == t)
    return sum(sum(v) / len(v) for v in per.values()) / len(per)


def macro_f1(pred, truth, k):
    f = []
    for c in set(truth):
        tp = sum(p == c and t == c for p, t in zip(pred, truth))
        fp = sum(p == c and t != c for p, t in zip(pred, truth))
        fn = sum(p != c and t == c for p, t in zip(pred, truth))
        f.append(2 * tp / (2 * tp + fp + fn) if tp + fp + fn else 0.0)
    return sum(f) / len(f)


def brier(P, T):
    return sum(sum((p[c] - (c == t)) ** 2 for c in range(len(p))) for p, t in zip(P, T)) / len(T)


def ece(P, T, bins=10):
    conf = [max(p) for p in P]
    corr = [argmax(p) == t for p, t in zip(P, T)]
    tot = 0.0
    for b in range(bins):
        idx = [i for i, c in enumerate(conf) if b / bins < c <= (b + 1) / bins or (b == 0 and c == 0)]
        if idx:
            tot += len(idx) / len(P) * abs(sum(corr[i] for i in idx) / len(idx) - sum(conf[i] for i in idx) / len(idx))
    return tot


def auc(scores, labels):
    pos = sorted(s for s, l in zip(scores, labels) if l)
    neg = sorted(s for s, l in zip(scores, labels) if not l)
    if not pos or not neg:
        return float("nan")
    import bisect
    wins = sum(bisect.bisect_left(neg, s) + 0.5 * (bisect.bisect_right(neg, s) - bisect.bisect_left(neg, s)) for s in pos)
    return wins / (len(pos) * len(neg))


def qwk(pred, truth, k):
    n = len(truth)
    O = [[0] * k for _ in range(k)]
    for p, t in zip(pred, truth):
        O[t][p] += 1
    rt = [sum(O[i]) for i in range(k)]
    rp = [sum(O[i][j] for i in range(k)) for j in range(k)]
    num = sum(((i - j) ** 2 / (k - 1) ** 2) * O[i][j] for i in range(k) for j in range(k))
    den = sum(((i - j) ** 2 / (k - 1) ** 2) * rt[i] * rp[j] / n for i in range(k) for j in range(k))
    return 1 - num / den if den else float("nan")


def task_metrics(task, P_raw, T, k):
    P = [p if p is not None else [1 / k] * k for p in P_raw]
    pred = [argmax(p) if r is not None else -1 for p, r in zip(P, P_raw)]
    conf = [max(p) for p in P]
    hi = [pr == t for pr, t, c in zip(pred, T, conf) if c >= 0.9]
    m = {"balanced_acc": balanced_acc(pred, T, k), "accuracy": sum(p == t for p, t in zip(pred, T)) / len(T),
         "macro_f1": macro_f1(pred, T, k), "brier": brier(P, T), "ece": ece(P, T),
         "log_loss": -sum(math.log(max(p[t], EPS)) for p, t in zip(P, T)) / len(T),
         "conf90_acc": sum(hi) / len(hi) if hi else None, "conf90_share": len(hi) / len(T),
         "refusals": sum(r is None for r in P_raw)}
    if k == 2:
        m["auc"] = auc([p[1] for p in P], T)
    if task in ("T4", "T5"):
        ok = [(p, t) for p, t in zip(pred, T) if p >= 0]
        m["qwk"] = qwk([p for p, _ in ok], [t for _, t in ok], k)
        m["within_1"] = sum(abs(p - t) <= 1 for p, t in ok) / len(T)
    return m


def mean_metrics(ms):
    out = {}
    for key in ms[0]:
        vals = [m[key] for m in ms if m[key] is not None and not (isinstance(m[key], float) and math.isnan(m[key]))]
        out[key] = sum(vals) / len(vals) if vals else None
    return out


def holm(pvals):
    order = sorted(range(len(pvals)), key=pvals.__getitem__)
    adj, run = [0.0] * len(pvals), 0.0
    for r, i in enumerate(order):
        run = max(run, min(1.0, (len(pvals) - r) * pvals[i]))
        adj[i] = run
    return adj


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=2000)
    a = ap.parse_args()
    items = {}
    for l in open(os.path.join(HERE, "data", "dataset.jsonl")):
        r = json.loads(l)
        items[r["id"]] = r
    res = defaultdict(dict)  # model -> (id, variant) -> record
    for fn in sorted(os.listdir(os.path.join(HERE, "results"))):
        for l in open(os.path.join(HERE, "results", fn)):
            r = json.loads(l)
            res[r["model"]][(r["id"], r["variant"])] = r
    models = sorted(res)

    # items with an API error for any model in any main variant are dropped for everyone
    def ok(i):
        return all((i, v) in res[m] and not res[m][(i, v)]["error"] for m in models for v in VARIANTS)
    kept = [i for i in items if ok(i)]
    dropped = len(items) - len(kept)
    by_task = {t: [i for i in kept if items[i]["task"] == t] for t in TASKS}
    by_task = {t: ids for t, ids in by_task.items() if ids}
    tasks = list(by_task)

    K = {t: len(classes(t)) for t in tasks}
    truth = {t: [classes(t).index(items[i]["truth"]) for i in by_task[t]] for t in tasks}
    P = {(m, t, v): [probs(t, res[m][(i, v)]["answer"], K[t]) for i in by_task[t]] for m in models for t in tasks for v in VARIANTS}

    # ---- per-task metrics (mean over phrasings) + phrasing sensitivity
    M, per_variant = {}, {}
    for m in models:
        for t in tasks:
            vs = {v: task_metrics(t, P[(m, t, v)], truth[t], K[t]) for v in VARIANTS}
            per_variant[(m, t)] = {v: vs[v]["balanced_acc"] for v in VARIANTS}
            M[(m, t)] = mean_metrics(list(vs.values()))

    # ---- bootstrap: per-item correctness averaged over phrasings, resampled within each class
    corr = {(m, t): [sum((p is not None and argmax(p) == tr) for p in col) / len(VARIANTS)
                     for col, tr in zip(zip(*[P[(m, t, v)] for v in VARIANTS]), truth[t])]
            for m in models for t in tasks}
    strata = {t: defaultdict(list) for t in tasks}
    for t in tasks:
        for j, tr in enumerate(truth[t]):
            strata[t][tr].append(j)
    rng = random.Random(7)
    boot = {m: {t: [] for t in tasks + ["overall"]} for m in models}
    boot_skill = {m: [] for m in models}  # chance-corrected, for SCORING.md quality pillar
    for _ in range(a.boot):
        samp = {t: {c: [ix[rng.randrange(len(ix))] for _ in ix] for c, ix in strata[t].items()} for t in tasks}
        for m in models:
            tot, sk = 0.0, 0.0
            for t in tasks:
                cv = corr[(m, t)]
                ba = sum(sum(cv[j] for j in s) / len(s) for s in samp[t].values()) / len(samp[t])
                boot[m][t].append(ba)
                tot += ba
                sk += (ba - 1 / K[t]) / (1 - 1 / K[t])
            boot[m]["overall"].append(tot / len(tasks))
            boot_skill[m].append(100 * sk / len(tasks))

    def point(m, t):
        if t == "overall":
            return sum(point(m, x) for x in tasks) / len(tasks)
        cv = corr[(m, t)]
        return sum(sum(cv[j] for j in s) / len(s) for s in strata[t].values()) / len(strata[t])

    def ci(xs):
        s = sorted(xs)
        return s[int(0.025 * len(s))], s[int(0.975 * len(s)) - 1]

    scopes = tasks + ["overall"]
    pairs = list(combinations(models, 2))
    pair_stats = {}
    for sc in scopes:
        raw = []
        for x, y in pairs:
            d = [p - q for p, q in zip(boot[x][sc], boot[y][sc])]
            raw.append(min(1.0, 2 * min(sum(v <= 0 for v in d), sum(v >= 0 for v in d)) / len(d)))
        adj = holm(raw)
        for (x, y), r, h in zip(pairs, raw, adj):
            pair_stats[(sc, x, y)] = {"diff": point(x, sc) - point(y, sc), "p": r, "p_holm": h}

    ranks = {}
    for sc in scopes:
        rk = {m: [] for m in models}
        for b in range(a.boot):
            order = sorted(models, key=lambda m: -boot[m][sc][b])
            for r, m in enumerate(order, 1):
                rk[m].append(r)
        ranks[sc] = {m: {"p_first": rk[m].count(1) / a.boot, "rank_ci": ci(rk[m])} for m in models}

    def verdict(sc):
        order = sorted(models, key=lambda m: -point(m, sc))
        top = [order[0]]
        for m in order[1:]:
            key = (sc, order[0], m) if (sc, order[0], m) in pair_stats else (sc, m, order[0])
            if pair_stats[key]["p_holm"] >= 0.05:
                top.append(m)
        return order, top

    # ---- baselines
    def rule_pred(t, i):
        it = items[i]
        if t == "T1":
            txt = (it["state"]["title"] + " " + it["state"]["body"]).lower()
            return 0 if re.search(r"\b(add|support|allow|option|feature request|would be (nice|great)|please consider|ability to)\b", txt) else 1
        if t == "T2":
            return 0 if it["meta"].get("author_association") in ("NONE", "FIRST_TIMER", "FIRST_TIME_CONTRIBUTOR") else 1
        if t == "T3":
            cl = classes("T3")
            hits = [c for c in cl if c.lower() in it["state"]["summary"].lower()]
            return cl.index(max(hits, key=len)) if hits else cl.index(Counter(items[x]["truth"] for x in by_task["T3"]).most_common(1)[0][0])
        return None

    baselines = {}
    for t in tasks:
        maj = Counter(truth[t]).most_common(1)[0][0]
        freq = [truth[t].count(c) / len(truth[t]) for c in range(K[t])]
        b = {"prior_balanced_acc": balanced_acc([maj] * len(truth[t]), truth[t], K[t]),
             "prior_brier": brier([freq] * len(truth[t]), truth[t])}
        rp = [rule_pred(t, i) for i in by_task[t]]
        if rp[0] is not None:
            b["rule_balanced_acc"] = balanced_acc(rp, truth[t], K[t])
        baselines[t] = b

    # ---- repeatability (R1 vs P1)
    repeat = {}
    for m in models:
        agree, diff, n = 0, 0.0, 0
        for (i, v), r in res[m].items():
            if v != "R1" or r["error"] or i not in items:
                continue
            p0 = res[m].get((i, "P1"))
            if not p0 or p0["error"]:
                continue
            t = items[i]["task"]
            a1, a0 = probs(t, r["answer"], K.get(t, 2)), probs(t, p0["answer"], K.get(t, 2))
            if a1 is None or a0 is None:
                continue
            n += 1
            agree += argmax(a1) == argmax(a0)
            diff += sum(abs(x - y) for x, y in zip(a1, a0)) / 2
        repeat[m] = {"n": n, "same_answer": agree / n if n else None, "mean_prob_shift": diff / n if n else None}

    # ---- ops
    ops = {}
    for m in models:
        rs = [r for (i, v), r in res[m].items() if v in VARIANTS]
        lat = sorted(r["latency_ms"] for r in rs if r["latency_ms"])
        cost = [r["usage"]["cost"] for r in rs if r.get("usage") and r["usage"].get("cost") is not None]
        ops[m] = {"requests": len(rs), "api_errors": sum(bool(r["error"]) for r in rs),
                  "p50_ms": lat[len(lat) // 2] if lat else None, "p95_ms": lat[int(0.95 * len(lat))] if lat else None,
                  "cost_per_1k": 1000 * sum(cost) / len(cost) if cost else None,
                  "providers": sorted({r["provider"] for r in rs if r.get("provider")})}

    # ---- label audit: all models' (phrasing-averaged) answer agrees, and differs from the label
    audit = []
    for t in tasks:
        for j, i in enumerate(by_task[t]):
            answers = set()
            for m in models:
                cols = [P[(m, t, v)][j] for v in VARIANTS if P[(m, t, v)][j] is not None]
                if not cols:
                    answers.add(None)
                    continue
                avg = [sum(c[x] for c in cols) / len(cols) for x in range(K[t])]
                answers.add(argmax(avg))
            if len(answers) == 1 and None not in answers and next(iter(answers)) != truth[t][j]:
                audit.append([t, i, items[i]["source"], items[i]["truth"], classes(t)[next(iter(answers))]])
    with open(os.path.join(HERE, "label_audit.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task", "id", "source", "label", "all_models_say"])
        w.writerows(audit)
    t4_changed = [items[i]["meta"].get("severity_changes", 0) > 0 for i in by_task.get("T4", [])]

    # T3 exploratory: bugs whose title does NOT name the component
    t3_hard = {}
    if "T3" in tasks:
        idx = [j for j, i in enumerate(by_task["T3"]) if items[i]["truth"].lower() not in items[i]["state"]["summary"].lower()]
        for m in models:
            ms = [task_metrics("T3", [P[(m, "T3", v)][j] for j in idx], [truth["T3"][j] for j in idx], K["T3"])["balanced_acc"] for v in VARIANTS]
            t3_hard[m] = sum(ms) / len(ms)
        t3_hard["_n"] = len(idx)

    out = {"models": models, "tasks": tasks, "n": {t: len(by_task[t]) for t in tasks}, "dropped_items": dropped,
           "point": {m: {sc: point(m, sc) for sc in scopes} for m in models},
           "ci": {m: {sc: ci(boot[m][sc]) for sc in scopes} for m in models},
           "metrics": {m: {t: M[(m, t)] for t in tasks} for m in models},
           "per_variant": {m: {t: per_variant[(m, t)] for t in tasks} for m in models},
           "pairs": {f"{sc}|{x}|{y}": v for (sc, x, y), v in pair_stats.items()},
           "ranks": ranks, "verdict": {sc: verdict(sc)[1] for sc in scopes},
           "baselines": baselines, "repeat": repeat, "ops": ops, "label_audit_count": len(audit),
           "label_audit_by_task": dict(Counter(r[0] for r in audit)),
           "t4_severity_changed_share": sum(t4_changed) / len(t4_changed) if t4_changed else None,
           "t3_title_doesnt_name_component": t3_hard,
           "skill_point": {m: 100 * sum((point(m, t) - 1 / K[t]) / (1 - 1 / K[t]) for t in tasks) / len(tasks) for m in models},
           "boot_skill": boot_skill}
    json.dump(out, open(os.path.join(HERE, "results.json"), "w"), indent=1, default=str)
    write_report(out)


def pct(x, d=1):
    return "-" if x is None else f"{100 * x:.{d}f}%"


def f3(x, d=3):
    return "-" if x is None else f"{x:.{d}f}"


def short(m):
    return m.split("/")[-1]


def write_report(o):
    models, tasks = o["models"], o["tasks"]
    order = sorted(models, key=lambda m: -o["point"][m]["overall"])
    L = ["# v2 results (generated by score_v2.py)", "",
         f"Items per task: {o['n']}. Dropped for API errors: {o['dropped_items']}. Each item asked in 3 phrasings.", "",
         "## Overall: mean balanced accuracy over all tasks", "",
         "| Rank | Model | Balanced acc. (95% CI) | P(rank #1) | Rank 95% CI | Mean Brier | Mean ECE | p50 / p95 latency | Cost / 1k | Same answer on repeat |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for r, m in enumerate(order, 1):
        mb = sum(o["metrics"][m][t]["brier"] for t in tasks) / len(tasks)
        me = sum(o["metrics"][m][t]["ece"] for t in tasks) / len(tasks)
        op, ci, rk = o["ops"][m], o["ci"][m]["overall"], o["ranks"]["overall"][m]
        L.append(f"| {r} | {m} | {pct(o['point'][m]['overall'])} ({pct(ci[0])}-{pct(ci[1])}) | {pct(rk['p_first'], 0)} | "
                 f"{rk['rank_ci'][0]}-{rk['rank_ci'][1]} | {f3(mb)} | {f3(me)} | {f3(op['p50_ms'], 0)} / {f3(op['p95_ms'], 0)} ms | "
                 f"${f3(op['cost_per_1k'], 4)} | {pct(o['repeat'][m]['same_answer'])} |")
    top = o["verdict"]["overall"]
    L += ["", f"**Verdict (pre-registered rule):** " + (f"{top[0]} is the best overall." if len(top) == 1 else
          f"no single best model; statistically tied top group: {', '.join(top)}."), ""]
    for t in tasks:
        b = o["baselines"][t]
        L += [f"## {t}. {TASK_NAMES[t]} (n = {o['n'][t]})", "",
              f"Baselines: always-majority {pct(b['prior_balanced_acc'])}" +
              (f"; shortcut rule {pct(b['rule_balanced_acc'])}" if "rule_balanced_acc" in b else ""), "",
              "| Model | Balanced acc. (95% CI) | P1 / P2 / P3 | Macro-F1 | " + ("AUC | " if t in ("T1", "T2") else "QWK | Within 1 | " if t in ("T4", "T5") else "") +
              "Brier | ECE | Acc. when >=90% sure (share) | Refusals |",
              "|---|---|---|---|" + ("---|" if t in ("T1", "T2") else "---|---|" if t in ("T4", "T5") else "") + "---|---|---|---|"]
        for m in sorted(models, key=lambda m: -o["point"][m][t]):
            x, ci, pv = o["metrics"][m][t], o["ci"][m][t], o["per_variant"][m][t]
            extra = f"{f3(x.get('auc'))} | " if t in ("T1", "T2") else f"{f3(x.get('qwk'))} | {pct(x.get('within_1'))} | " if t in ("T4", "T5") else ""
            L.append(f"| {m} | {pct(o['point'][m][t])} ({pct(ci[0])}-{pct(ci[1])}) | {' / '.join(pct(pv[v], 0) for v in VARIANTS)} | "
                     f"{f3(x['macro_f1'])} | {extra}{f3(x['brier'])} | {f3(x['ece'])} | {pct(x['conf90_acc'])} ({pct(x['conf90_share'], 0)}) | {f3(x['refusals'], 1)} |")
        tt = o["verdict"][t]
        L += ["", "Top group (not significantly different from #1 after Holm): " + ", ".join(short(m) for m in tt), ""]
    L += ["## Significant pairwise differences, overall (Holm-adjusted p < 0.05)", ""]
    sig = [(k, v) for k, v in o["pairs"].items() if k.startswith("overall|") and v["p_holm"] < 0.05]
    for k, v in sorted(sig, key=lambda kv: -abs(kv[1]["diff"])):
        _, x, y = k.split("|")
        better, worse = (x, y) if v["diff"] > 0 else (y, x)
        L.append(f"- {short(better)} > {short(worse)} by {100 * abs(v['diff']):.1f} pts (adj. p = {v['p_holm']:.3f})")
    if not sig:
        L.append("- none")
    L += ["", "## Data quality", "",
          f"- Items where all 7 models agree with each other but not with the label: {o['label_audit_count']} {o['label_audit_by_task']} (label_audit.csv, for human review).",
          f"- T4: share of bugs whose severity was later changed by triagers: {pct(o['t4_severity_changed_share'])}."]
    h = o["t3_title_doesnt_name_component"]
    if h:
        L.append(f"- T3 exploratory (not pre-registered): balanced accuracy on the {h['_n']} bugs whose title does not name the component: " +
                 ", ".join(f"{short(m)} {pct(h[m])}" for m in sorted(models, key=lambda m: -h[m])))
    open(os.path.join(HERE, "report_v2.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
