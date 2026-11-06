"""Collect the frozen v2 dataset (see METHODOLOGY.md section 3).

Usage: python3 collect_v2.py   -> data/dataset.jsonl, data/components.json (+ .sha256)
"""
import concurrent.futures as cf
import hashlib
import json
import os
import random
import re
import sys
import urllib.parse
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from collect import clean as clean_v1, gh, gh_search, http_json, is_bot  # noqa: E402  (v1 helpers)

DATA = os.path.join(HERE, "data")
FROM, TO, PR_TO = "2026-09-15", "2026-11-05", "2026-10-29"
SEED = 20261107
MAX_CHARS = 4000
rng = random.Random(SEED)


def log(*a):
    print(*a, file=sys.stderr, flush=True)


# --------------------------------------------------------------------------- cleaning
def clean_issue(text):
    """v1 cleaning + drop template headings and bot commands, which reveal the issue type."""
    text = clean_v1(text)
    text = "\n".join(l for l in text.splitlines()
                     if not re.match(r"^\s*#{1,6}\s", l)          # template headings ("### What happened?")
                     and not re.match(r"^\s*/[a-z-]+(\s|$)", l))  # prow commands ("/kind bug", "/sig node")
    return re.sub(r"\n{3,}", "\n\n", text).strip()[:MAX_CHARS]


CVSS_PATTERNS = [
    r"CVSS:\d\.\d/[A-Z:/]+",                         # vectors
    r"(?i)\bcvss(\s*v?\d(\.\d)?)?\s*(base\s*)?(score)?\s*[:=]?\s*\d+(\.\d)?",
    r"(?i)\bcvss\w*",
    r"(?im)^.*\b(severity|base score)\b\s*[:=].*$",  # "Severity: High" lines
    r"(?i)\(\s*\d{1,2}\.\d\s*\)",                    # "(9.8)"
]


def clean_advisory(text):
    text = text or ""
    for p in CVSS_PATTERNS:
        text = re.sub(p, "", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()[:MAX_CHARS]


def take(rows, n):
    rows = list(rows)
    rng.shuffle(rows)
    return rows[:n]


# --------------------------------------------------------------------------- T1
def t1():
    repos = {
        "microsoft/vscode": ("bug", "feature-request"),
        "kubernetes/kubernetes": ("kind/bug", "kind/feature"),
    }
    out = []
    for repo, (bl, fl) in repos.items():
        pools = {}
        for label, other, truth in ((bl, fl, True), (fl, bl, False)):
            items = gh_search(f'repo:{repo} is:issue label:"{label}" -label:"{other}" created:{FROM}..{TO}', 450)
            rows = []
            for i in items:
                if is_bot(i["user"]["login"]):
                    continue
                body = clean_issue(i.get("body"))
                if len(body) < 30:
                    continue
                rows.append({"id": f"T1:{repo}#{i['number']}", "task": "T1", "source": i["html_url"],
                             "created_at": i["created_at"],
                             "state": {"repository": repo, "title": i["title"], "body": body},
                             "truth": truth, "meta": {}})
            pools[truth] = rows
        n = min(len(pools[True]), len(pools[False]))  # balance within each repo (no repo/label confound)
        out += take(pools[True], n) + take(pools[False], n)
        log(f"T1 {repo}: bugs {len(pools[True])}, features {len(pools[False])} -> {n}+{n}")
    return out


# --------------------------------------------------------------------------- T2
def t2():
    repos = ["microsoft/vscode", "vercel/next.js", "microsoft/TypeScript"]
    out = []
    for repo in repos:
        pools = {}
        for merged in (True, False):
            q = f"repo:{repo} is:pr is:closed {'is:merged' if merged else 'is:unmerged'} draft:false created:{FROM}..{PR_TO}"
            pools[merged] = [i for i in gh_search(q, 450) if not is_bot(i["user"]["login"])]
        n = min(120, len(pools[True]), len(pools[False]))
        pick = [(m, i) for m in (True, False) for i in take(pools[m], n)]
        with cf.ThreadPoolExecutor(6) as ex:
            details = list(ex.map(lambda mi: gh(f"repos/{repo}/pulls/{mi[1]['number']}"), pick))
        for (merged, i), p in zip(pick, details):
            out.append({"id": f"T2:{repo}#{i['number']}", "task": "T2", "source": i["html_url"],
                        "created_at": i["created_at"],
                        "state": {"repository": repo, "title": p["title"],
                                  "description": clean_v1(p.get("body")) or "(no description)",
                                  "base_branch": p["base"]["ref"], "changed_files": p.get("changed_files"),
                                  "additions": p.get("additions"), "deletions": p.get("deletions"),
                                  "commits": p.get("commits")},
                        "truth": merged,
                        "meta": {"author_association": p.get("author_association")}})  # rule baseline only
        log(f"T2 {repo}: merged {len(pools[True])}, unmerged {len(pools[False])} -> {n}+{n}")
    return out


# --------------------------------------------------------------------------- Firefox (T3, T4)
def bz(path, **params):
    return http_json("https://bugzilla.mozilla.org/rest/" + path + "?" + urllib.parse.urlencode(params, doseq=True))


def bz_desc(bug_id):
    c = bz(f"bug/{bug_id}/comment")["bugs"][str(bug_id)]["comments"]
    return clean_v1(c[0]["text"]) if c else ""


def bz_sev_changes(bug_id):
    """How many times severity was changed after it was first set to a real value."""
    hist = bz(f"bug/{bug_id}/history")["bugs"][0]["history"]
    changes = [ch for h in hist for ch in h["changes"] if ch["field_name"] == "severity"]
    real = [c for c in changes if c["removed"] not in ("--", "", "normal", "N/A")]
    return len(real)


def firefox():
    comps = bz("product/Firefox", include_fields="components.name,components.description,components.is_active")["products"][0]["components"]
    desc = {c["name"]: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", c["description"])).strip() for c in comps if c["is_active"]}
    bugs = bz("bug", product="Firefox", creation_time=FROM,
              include_fields="id,severity,component,summary,creation_time", limit=0)["bugs"]
    bugs = [b for b in bugs if b["creation_time"][:10] <= TO]
    counts = Counter(b["component"] for b in bugs)
    keep = sorted(c for c, n in counts.items() if n >= 10 and c not in ("General", "Untriaged") and c in desc)
    components = {c: desc[c] for c in keep}
    json.dump(components, open(os.path.join(DATA, "components.json"), "w"), indent=1, sort_keys=True)
    log(f"Firefox: {len(bugs)} bugs, {len(keep)} components with >=10")

    by_comp = defaultdict(list)
    for b in bugs:
        if b["component"] in components:
            by_comp[b["component"]].append(b)
    t3_pick = [b for c in keep for b in take(by_comp[c], 15)]

    sev = defaultdict(list)
    for b in bugs:
        sev[b["severity"]].append(b)
    hi = sev["S1"] + sev["S2"]
    rest = max(0, (300 - len(hi)) // 2)
    t4_pick = hi + take(sev["S3"], rest) + take(sev["S4"], rest)

    ids = {b["id"] for b in t3_pick + t4_pick}
    log(f"Firefox: fetching {len(ids)} descriptions + {len(t4_pick)} histories")
    with cf.ThreadPoolExecutor(8) as ex:
        descs = dict(zip(ids, ex.map(bz_desc, ids)))
        log("  descriptions done")
        sev_hist = dict(zip([b["id"] for b in t4_pick], ex.map(bz_sev_changes, [b["id"] for b in t4_pick])))
        log("  histories done")

    def row(task, b, truth, meta):
        return {"id": f"{task}:bz{b['id']}", "task": task,
                "source": f"https://bugzilla.mozilla.org/show_bug.cgi?id={b['id']}", "created_at": b["creation_time"],
                "state": {"product": "Firefox", "summary": b["summary"], "description": descs[b["id"]]},
                "truth": truth, "meta": meta}

    t3 = [row("T3", b, b["component"], {}) for b in t3_pick if len(descs[b["id"]]) >= 30]
    t4 = [row("T4", b, b["severity"], {"severity_changes": sev_hist[b["id"]]}) for b in t4_pick if len(descs[b["id"]]) >= 30]
    log(f"T3: {len(t3)} items over {len(keep)} components;  T4: {len(t4)} {Counter(r['truth'] for r in t4)}")
    return t3, t4


# --------------------------------------------------------------------------- T5
def t5():
    # the advisories API is cursor-paginated (page= is ignored); let gh follow the Link headers
    import subprocess
    cmd = ["gh", "api", "--paginate", "-X", "GET", "/advisories", "-f", "type=reviewed",
           "-f", f"published={FROM}..{TO}", "-f", "per_page=100", "--jq", ".[] | @json"]
    lines = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.splitlines()
    advs = list({a["ghsa_id"]: a for a in map(json.loads, lines)}.values())
    log(f"  advisories fetched: {len(advs)}")
    pools = defaultdict(list)
    for a in advs:
        text = clean_advisory(a.get("description"))
        if len(text) < 50 or a["severity"] not in ("low", "medium", "high", "critical"):
            continue
        pkgs = [f"{v['package']['ecosystem']}:{v['package']['name']}" for v in (a.get("vulnerabilities") or []) if v.get("package")]
        pools[a["severity"]].append({
            "id": f"T5:{a['ghsa_id']}", "task": "T5", "source": a["html_url"], "created_at": a["published_at"],
            "state": {"packages": pkgs[:5], "summary": clean_advisory(a.get("summary")), "description": text},
            "truth": a["severity"], "meta": {"cvss_score": (a.get("cvss") or {}).get("score")}})
    out = [r for s in ("low", "medium", "high", "critical") for r in take(pools[s], 120)]
    log(f"T5: {len(advs)} advisories; usable {dict((k, len(v)) for k, v in pools.items())} -> {Counter(r['truth'] for r in out)}")
    return out


def main():
    os.makedirs(DATA, exist_ok=True)
    cache = os.path.join(DATA, "_github_cache.json")
    if os.path.exists(cache):
        rows = json.load(open(cache))
        log(f"T1/T2 from cache: {len(rows)}")
    else:
        rows = t1() + t2()
        json.dump(rows, open(cache, "w"))
    a, b = firefox()
    rows += a + b + t5()
    path = os.path.join(DATA, "dataset.jsonl")
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    for p in (path, os.path.join(DATA, "components.json")):
        open(p + ".sha256", "w").write(hashlib.sha256(open(p, "rb").read()).hexdigest() + "\n")
    log(f"wrote {len(rows)} items: {Counter(r['task'] for r in rows)}")


if __name__ == "__main__":
    main()
