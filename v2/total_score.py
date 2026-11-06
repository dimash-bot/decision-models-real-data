"""Total score exactly as pre-registered in SCORING.md. Needs results.json from score_v2.py.

Writes total_score.json and total_score.md.
"""
import json
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
C = os.path.join(HERE, "company")
W = {"quality": 0.45, "efficiency": 0.20, "trust": 0.20, "reviews": 0.10, "bonus": 0.05}


def clip(x, lo=0.0, hi=100.0):
    return max(lo, min(hi, x))


def log_score(x, zero_at, full_at):
    """0 at zero_at, 100 at full_at, log scale (works for increasing or decreasing)."""
    return clip(100 * math.log10(x / zero_at) / math.log10(full_at / zero_at))


def main():
    R = json.load(open(os.path.join(HERE, "results.json")))
    inp = json.load(open(os.path.join(C, "inputs.json")))["models"]
    bonus = json.load(open(os.path.join(C, "signup_bonus.json")))
    hn = json.load(open(os.path.join(C, "hn_mentions_labels.json")))
    models, tasks = R["models"], R["tasks"]

    # ---- Quality: 0.8 skill + 0.2 calibration (Brier vs prior Brier)
    def calib(m):
        ts = [t for t in tasks if R["baselines"][t]["prior_brier"] > 0]  # guard: single-class partial data
        return 100 * sum(1 - R["metrics"][m][t]["brier"] / R["baselines"][t]["prior_brier"] for t in ts) / len(ts)
    cal = {m: calib(m) for m in models}
    Q = {m: 0.8 * R["skill_point"][m] + 0.2 * cal[m] for m in models}
    Qboot = {m: [0.8 * s + 0.2 * cal[m] for s in R["boot_skill"][m]] for m in models}

    # ---- Efficiency
    def eff(m, cost=None):
        o = R["ops"][m]
        c = cost if cost is not None else o["cost_per_1k"]
        return 0.6 * log_score(c, 0.5, 0.005) + 0.4 * log_score(o["p50_ms"], 5000, 100)
    E = {m: eff(m) for m in models}

    # ---- Trust (checklist, 100 points)
    def trust(m):
        x, o, rep = inp[m], R["ops"][m], R["repeat"][m]
        yn = lambda v, pts, good: pts if v == good else pts / 2 if v in ("conflicting", "unclear", "partial") else 0
        pts = yn(x["training"], 20, "no") + yn(x["retains"], 15, "no") + (10 if x["zdr"] else 0)
        pts += yn(x["weights"], 15, "yes")
        pts += {"permissive": 10, "restricted": 5}.get(x["licence"], 0)
        pts += yn(x["disclosed"], 10, "yes")
        refusals = sum(R["metrics"][m][t]["refusals"] for t in tasks) * 3  # metrics are per-phrasing means
        ok_rate = 1 - (o["api_errors"] + refusals) / o["requests"]
        pts += clip(10 * (ok_rate - 0.95) / 0.05, 0, 10)
        pts += clip(10 * ((rep["same_answer"] or 0) - 0.90) / 0.10, 0, 10)
        return pts, ok_rate
    T, okr = {}, {}
    for m in models:
        T[m], okr[m] = trust(m)

    # ---- Reviews: usage (6/10) + HN discussion (4/10)
    disc = {}
    for fam, ms in hn.items():
        rel = [x for x in ms if x.get("about_product")]
        pos = sum(x["sentiment"] == "positive" for x in rel)
        neg = sum(x["sentiment"] == "negative" for x in rel)
        disc[fam] = {"n": len(rel), "pos": pos, "neg": neg,
                     "score": 50 + 50 * (pos - neg) / len(rel) if len(rel) >= 10 else 50.0,
                     "insufficient": len(rel) < 10}
    Rv = {m: 0.6 * log_score(inp[m]["weekly_requests"], 1e6, 1e10) + 0.4 * disc[inp[m]["family"]]["score"] for m in models}

    # ---- Signup bonus
    def bonus_score(m):
        credit = bonus[inp[m]["provider"]]["signup_credit_usd"]
        if not credit:
            return 0.0, 0
        free = credit / (inp[m]["direct_price_per_m"] * 1200 / 1e6)
        return clip(100 * math.log10(1 + free) / math.log10(1 + 1e6)), int(free)
    B, free_dec = {}, {}
    for m in models:
        B[m], free_dec[m] = bonus_score(m)

    pillars = {m: {"quality": Q[m], "efficiency": E[m], "trust": T[m], "reviews": Rv[m], "bonus": B[m]} for m in models}

    def total(p, w):
        return sum(w[k] * p[k] for k in w)

    tot = {m: total(pillars[m], W) for m in models}
    # 95% interval from the quality bootstrap
    nb = len(next(iter(Qboot.values())))
    tboot = {m: sorted(tot[m] + W["quality"] * (q - Q[m]) for q in Qboot[m]) for m in models}
    first = {m: 0 for m in models}
    for b in range(nb):
        best = max(models, key=lambda m: tot[m] + W["quality"] * (Qboot[m][b] - Q[m]))
        first[best] += 1

    # ---- Sensitivity
    def ranking(w, pil=pillars):
        return sorted(models, key=lambda m: -total(pil[m], w))
    scen = {
        "Main weights (45/20/20/10/5)": ranking(W),
        "Quality only": ranking({"quality": 1}),
        "Equal weights (20% each)": ranking({k: 0.2 for k in W}),
        "No signup bonus (rescaled)": ranking({k: v / 0.95 for k, v in W.items() if k != "bonus"}),
    }
    if "nace-ai/drex-max" in models:
        pil2 = json.loads(json.dumps(pillars))
        m = "nace-ai/drex-max"
        pil2[m]["efficiency"] = eff(m, cost=R["ops"][m]["cost_per_1k"] * inp[m]["list_price_per_m_openrouter"] / 0.06)
        scen["Drex Max at list price (no 50% promo)"] = ranking(W, pil2)
    rng = random.Random(11)
    wins = {m: 0 for m in models}
    N = 10000
    for _ in range(N):
        e = [-math.log(1 - rng.random()) for _ in W]  # uniform over the weight simplex
        w = {k: v / sum(e) for k, v in zip(W, e)}
        wins[ranking(w)[0]] += 1

    order = ranking(W)
    best = order[0]
    verdict = (f"{best} is best overall: #1 under the main weights and in {100 * wins[best] / N:.0f}% of random weightings."
               if wins[best] / N > 0.5 else
               f"No model is best overall. {best} is #1 under the main weights but wins only {100 * wins[best] / N:.0f}% of "
               f"random weightings, so the winner depends on what you value.")

    out = {"weights": W, "pillars": pillars, "total": tot,
           "total_ci": {m: (tboot[m][int(0.025 * nb)], tboot[m][int(0.975 * nb) - 1]) for m in models},
           "p_first_quality_uncertainty": {m: first[m] / nb for m in models},
           "random_weight_wins": {m: wins[m] / N for m in models}, "scenarios": scen, "verdict": verdict,
           "inputs": {"discussion": disc, "free_decisions": free_dec, "answered_ok_rate": okr, "calibration": cal,
                      "skill": R["skill_point"]}}
    json.dump(out, open(os.path.join(HERE, "total_score.json"), "w"), indent=1)

    s = lambda m: m.split("/")[-1]
    L = ["# Total score (SCORING.md)", "",
         "| Rank | Model | **Total** (95% CI) | Quality 45% | Efficiency 20% | Trust 20% | Reviews 10% | Signup bonus 5% | Wins under random weights |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r, m in enumerate(order, 1):
        p, ci = pillars[m], out["total_ci"][m]
        L.append(f"| {r} | {m} | **{tot[m]:.1f}** ({ci[0]:.1f}-{ci[1]:.1f}) | {p['quality']:.1f} | {p['efficiency']:.1f} | "
                 f"{p['trust']:.1f} | {p['reviews']:.1f} | {p['bonus']:.1f} | {100 * wins[m] / N:.0f}% |")
    L += ["", f"**Verdict (pre-registered rule):** {verdict}", "", "## Does the ranking depend on the weights?", "",
          "| Scenario | #1 | #2 | #3 |", "|---|---|---|---|"]
    for k, v in scen.items():
        L.append(f"| {k} | {s(v[0])} | {s(v[1])} | {s(v[2])} |")
    L += ["", "## Inputs", "",
          "Discussion (Hacker News since 2026-09-01, relevant mentions; <10 = neutral 50): " +
          "; ".join(f"{f}: n={d['n']} (+{d['pos']}/-{d['neg']}){' insufficient' if d['insufficient'] else ''}" for f, d in disc.items()),
          "", "Free decisions from signup credit (provider's own price, 1,200-token request): " +
          ", ".join(f"{s(m)} {free_dec[m]:,}" for m in models)]
    open(os.path.join(HERE, "total_score.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
