"""Average confidence vs actual accuracy per model (reviewer request: replace the 90%+ view).

Confidence = probability the model gave to its chosen answer, averaged over every item and phrasing.
Accuracy = share of those answers that were right. Gap = confidence - accuracy (>0 = overconfident).
Writes confidence.json.
"""
import json
import os

from score_v2 import argmax, classes, probs
from tasks_v2 import TASKS, VARIANTS

HERE = os.path.dirname(os.path.abspath(__file__))
items = {json.loads(l)["id"]: json.loads(l) for l in open(os.path.join(HERE, "data", "dataset.jsonl"))}
out = {}
for fn in sorted(os.listdir(os.path.join(HERE, "results"))):
    recs = [json.loads(l) for l in open(os.path.join(HERE, "results", fn))]
    last = {(r["id"], r["variant"]): r for r in recs}
    model = recs[0]["model"]
    conf, corr, per = [], [], {}
    for (i, v), r in last.items():
        if v not in VARIANTS or r["error"] or i not in items:
            continue
        t = items[i]["task"]
        cl = classes(t)
        p = probs(t, r["answer"], len(cl))
        if p is None:
            continue
        c, ok = max(p), cl[argmax(p)] == items[i]["truth"]
        conf.append(c); corr.append(ok)
        per.setdefault(t, [[], []]); per[t][0].append(c); per[t][1].append(ok)
    out[model] = {"avg_confidence": sum(conf) / len(conf), "accuracy": sum(corr) / len(corr), "n": len(conf),
                  "by_task": {t: {"avg_confidence": sum(a) / len(a), "accuracy": sum(b) / len(b)} for t, (a, b) in per.items()}}
    out[model]["gap"] = out[model]["avg_confidence"] - out[model]["accuracy"]
json.dump(out, open(os.path.join(HERE, "confidence.json"), "w"), indent=1)
for m, x in sorted(out.items(), key=lambda kv: kv[1]["gap"]):
    print(f"{m:32} confidence {100*x['avg_confidence']:5.1f}%  accuracy {100*x['accuracy']:5.1f}%  gap {100*x['gap']:+5.1f}  (n={x['n']})")
