"""T6 from the ready-made NVD 2026 feed (Amendment 1). Appends to data/dataset.jsonl, writes data/cwes.json.

Usage: python3 collect_nvd.py   (after collect_v2.py; needs data/raw/nvdcve-2.0-2026.json.gz and cwec_latest.csv.zip)
"""
import csv
import gzip
import hashlib
import io
import json
import os
import random
import re
import zipfile
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
FROM, TO = "2026-09-15", "2026-11-06"
TOP_K, PER_CWE = 20, 25
rng = random.Random(20261108)


def clean(text):
    text = re.sub(r"CVSS:\d\.\d/[A-Z:/]+", "", text)
    text = re.sub(r"(?i)\bCWE-\d+\b:?", "", text)
    text = re.sub(r"(?i)\bcvss\w*(\s*v?\d(\.\d)?)?(\s*(base\s*)?score)?\s*[:=]?\s*(\d+(\.\d)?)?", "", text)
    return re.sub(r"\s+", " ", text).strip()[:4000]


def main():
    # MITRE CWE names + descriptions
    z = zipfile.ZipFile(os.path.join(RAW, "cwec_latest.csv.zip"))
    rows = csv.DictReader(io.TextIOWrapper(z.open(z.namelist()[0]), encoding="utf-8"))
    mitre = {f"CWE-{r['CWE-ID']}": (r["Name"], r["Description"]) for r in rows}

    feed = json.load(gzip.open(os.path.join(RAW, "nvdcve-2.0-2026.json.gz")))
    pool = defaultdict(list)
    for v in feed["vulnerabilities"]:
        c = v["cve"]
        if not (FROM <= c["published"][:10] <= TO) or c.get("vulnStatus") == "Rejected":
            continue
        cw = {d["value"] for w in c.get("weaknesses", []) for d in w["description"] if d["value"].startswith("CWE-")}
        desc = next((d["value"] for d in c.get("descriptions", []) if d["lang"] == "en"), "")
        if len(cw) != 1 or len(desc) < 40:
            continue
        cwe = cw.pop()
        if cwe in mitre:
            pool[cwe].append((c, desc))
    top = [cwe for cwe, _ in Counter({k: len(v) for k, v in pool.items()}).most_common(TOP_K)]
    cwes = {f"{k}: {mitre[k][0]}": mitre[k][1].strip() for k in top}  # option label = "CWE-79: Improper Neutralization ..."
    label = {k: f"{k}: {mitre[k][0]}" for k in top}
    json.dump(cwes, open(os.path.join(HERE, "data", "cwes.json"), "w"), indent=1, sort_keys=True)

    out = []
    for k in top:
        items = pool[k][:]
        rng.shuffle(items)
        for c, desc in items[:PER_CWE]:
            out.append({"id": f"T6:{c['id']}", "task": "T6", "source": f"https://nvd.nist.gov/vuln/detail/{c['id']}",
                        "created_at": c["published"], "state": {"description": clean(desc)},
                        "truth": label[k], "meta": {"source_identifier": c.get("sourceIdentifier")}})
    path = os.path.join(HERE, "data", "dataset.jsonl")
    kept = [l for l in open(path) if json.loads(l)["task"] != "T6"]  # idempotent re-runs
    with open(path, "w") as f:
        f.writelines(kept)
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    for p in (path, os.path.join(HERE, "data", "cwes.json")):
        open(p + ".sha256", "w").write(hashlib.sha256(open(p, "rb").read()).hexdigest() + "\n")
    print(f"T6: {len(out)} CVEs over {len(top)} CWEs; pool sizes {[(k, len(pool[k])) for k in top]}")


if __name__ == "__main__":
    main()
