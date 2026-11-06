"""Collect a frozen, real-world dataset for comparing decision models.

Tasks (ground truth = what maintainers actually decided):
  A  issue_type     microsoft/vscode issues: bug vs feature request     (noul)
  B  pr_merged      vscode / next.js / TypeScript PRs: merged or not     (noul)
  C  ff_component   Firefox bugs: which of 8 components                  (choice)
  D  ff_severity    Firefox bugs: S1..S4 severity                        (score)

Only items created on/after CREATED_FROM are used, so the models (released
Sep 18 - Oct 21 2026) cannot have seen them in training.

Usage:  python3 collect.py               -> data/dataset.jsonl (+ .sha256)
Needs:  `gh` logged in (GitHub token is read from `gh auth token`).
"""
import concurrent.futures as cf
import hashlib
import http.client
import json
import os
import random
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request

from tasks import FF_COMPONENTS, SEV_INDEX

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "dataset.jsonl")
CREATED_FROM = "2026-09-15"
CREATED_TO = "2026-11-05"
PR_CREATED_TO = "2026-10-29"  # give PRs at least a week to be resolved
PER_TASK = 300
MAX_CHARS = 4000
SEED = 20261106
UA = "decision-eval/1.0"

GH_TOKEN = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()


def http_json(url, headers=None, tries=5):
    h = {"User-Agent": UA, **(headers or {})}
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (403, 429, 500, 502, 503) and i < tries - 1:
                time.sleep(10 * (i + 1))
                continue
            raise
        except (urllib.error.URLError, OSError, ValueError, http.client.HTTPException):  # incl. IncompleteRead
            if i < tries - 1:
                time.sleep(5 * (i + 1))
                continue
            raise


def gh(path, **params):
    url = "https://api.github.com/" + path + ("?" + urllib.parse.urlencode(params) if params else "")
    return http_json(url, {"Authorization": "Bearer " + GH_TOKEN, "Accept": "application/vnd.github+json"})


def gh_search(q, limit):
    """GitHub search (max 1000 results). 30 req/min limit -> pause between pages."""
    items, page = [], 1
    per = 30  # 100-item pages (~900 KB) get truncated on this network
    while len(items) < limit and page * per <= 1000:
        r = gh("search/issues", q=q, per_page=per, page=page, sort="created", order="desc")
        items += r["items"]
        if len(r["items"]) < per:
            break
        page += 1
        time.sleep(2.2)
    time.sleep(2.2)
    return items[:limit]


# --------------------------------------------------------------------------- cleaning
LEAK_PATTERNS = [
    r"(?im)^\s*Type:\s*<b>.*?</b>\s*$",                       # VS Code issue reporter: "Type: <b>Bug</b>"
    r"(?im)^.*Does this issue occur when all extensions are disabled.*$",
    r"(?is)<details>.*?</details>",                             # system info / extension tables
    r"(?is)<!--.*?-->",                                         # template comments
    r"(?im)^\s*(VS ?Code version|OS version|Extensions?: none|Version:|Commit:|Date:|Electron:|Chromium:|Node\.js:|V8:|OS:).*$",
    r"(?im)^\s*(Modes|Remote OS version|Remote OS):.*$",
]


def clean(text):
    text = text or ""
    for p in LEAK_PATTERNS:
        text = re.sub(p, "", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "[image]", text)    # images: text-only test
    text = re.sub(r"<img[^>]*>", "[image]", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text[:MAX_CHARS]


def is_bot(login):
    return login.endswith("[bot]") or login in {"dependabot", "renovate", "vs-code-engineering", "vscodenpm"}


# --------------------------------------------------------------------------- A: issue type
def task_issue_type(rng):
    rng_q = f"created:{CREATED_FROM}..{CREATED_TO}"
    out = []
    for label, truth in (("bug", True), ("feature-request", False)):
        other = "feature-request" if label == "bug" else "bug"
        items = gh_search(f"repo:microsoft/vscode is:issue label:{label} -label:{other} {rng_q}", 450)
        items = [i for i in items if not is_bot(i["user"]["login"])]
        rows = []
        for i in items:
            body = clean(i.get("body"))
            if len(body) < 30:
                continue
            rows.append({
                "id": f"issue_type:vscode#{i['number']}",
                "task": "issue_type",
                "source": i["html_url"],
                "created_at": i["created_at"],
                "state": {"repository": "microsoft/vscode", "title": i["title"], "body": body},
                "truth": truth,
            })
        rng.shuffle(rows)
        out += rows[: PER_TASK // 2]
        print(f"  issue_type {label}: {len(rows)} usable, took {min(len(rows), PER_TASK // 2)}", file=sys.stderr)
    return out


# --------------------------------------------------------------------------- B: PR merged
PR_REPOS = ["microsoft/vscode", "vercel/next.js", "microsoft/TypeScript"]


def task_pr_merged(rng):
    rng_q = f"created:{CREATED_FROM}..{PR_CREATED_TO}"
    pools = {True: [], False: []}
    for repo in PR_REPOS:
        for merged in (True, False):
            q = f"repo:{repo} is:pr is:closed {'is:merged' if merged else 'is:unmerged'} draft:false {rng_q}"
            items = [i for i in gh_search(q, 400) if not is_bot(i["user"]["login"])]
            pools[merged] += [(repo, i) for i in items]
            print(f"  pr_merged {repo} merged={merged}: {len(items)}", file=sys.stderr)

    def detail(pair):
        repo, i = pair
        p = gh(f"repos/{repo}/pulls/{i['number']}")
        return repo, i, p

    out = []
    for merged in (True, False):
        pool = pools[merged]
        rng.shuffle(pool)
        pool = pool[: PER_TASK // 2 + 40]  # a few spare in case some are filtered
        with cf.ThreadPoolExecutor(6) as ex:
            details = list(ex.map(detail, pool))
        rows = []
        for repo, i, p in details:
            rows.append({
                "id": f"pr_merged:{repo}#{i['number']}",
                "task": "pr_merged",
                "source": i["html_url"],
                "created_at": i["created_at"],
                "state": {
                    "repository": repo,
                    "title": p["title"],
                    "description": clean(p.get("body")) or "(no description)",
                    "author_association": p.get("author_association"),
                    "base_branch": p["base"]["ref"],
                    "changed_files": p.get("changed_files"),
                    "additions": p.get("additions"),
                    "deletions": p.get("deletions"),
                    "commits": p.get("commits"),
                },
                "truth": merged,
            })
        out += rows[: PER_TASK // 2]
    return out


# --------------------------------------------------------------------------- C/D: Firefox bugs


def bz_bugs():
    q = urllib.parse.urlencode([
        ("product", "Firefox"), ("creation_time", CREATED_FROM),
        *[("bug_severity", s) for s in ("S1", "S2", "S3", "S4")],
        ("include_fields", "id,severity,component,summary,creation_time,type"), ("limit", "0"),
    ])
    bugs = http_json("https://bugzilla.mozilla.org/rest/bug?" + q)["bugs"]
    return [b for b in bugs if b["creation_time"][:10] <= CREATED_TO]


def bz_description(bug_id):
    r = http_json(f"https://bugzilla.mozilla.org/rest/bug/{bug_id}/comment")
    comments = r["bugs"][str(bug_id)]["comments"]
    return comments[0]["text"] if comments else ""


def ff_row(task, b, desc, truth):
    return {
        "id": f"{task}:bz{b['id']}",
        "task": task,
        "source": f"https://bugzilla.mozilla.org/show_bug.cgi?id={b['id']}",
        "created_at": b["creation_time"],
        "state": {"product": "Firefox", "summary": b["summary"], "description": desc},
        "truth": truth,
    }


def task_firefox(rng):
    bugs = bz_bugs()
    print(f"  firefox bugs since {CREATED_FROM}: {len(bugs)}", file=sys.stderr)
    comp_pool = [b for b in bugs if b["component"] in FF_COMPONENTS]
    rng.shuffle(comp_pool)
    # component: up to 40 per component (balanced as far as data allows)
    per = {}
    comp_pick = []
    for b in comp_pool:
        if per.get(b["component"], 0) < 40:
            per[b["component"]] = per.get(b["component"], 0) + 1
            comp_pick.append(b)
    # severity: all S1/S2, then equal S3/S4 to fill PER_TASK
    sev = {s: [b for b in bugs if b["severity"] == s] for s in SEV_INDEX}
    for s in sev:
        rng.shuffle(sev[s])
    hi = sev["S1"] + sev["S2"]
    rest = (PER_TASK - len(hi)) // 2
    sev_pick = hi + sev["S3"][:rest] + sev["S4"][:rest]

    need = {b["id"] for b in comp_pick + sev_pick}
    with cf.ThreadPoolExecutor(8) as ex:
        descs = dict(zip(need, ex.map(bz_description, need)))
    descs = {k: clean(v) for k, v in descs.items()}

    comp_rows = [ff_row("ff_component", b, descs[b["id"]], b["component"]) for b in comp_pick if len(descs[b["id"]]) >= 30]
    sev_rows = [ff_row("ff_severity", b, descs[b["id"]], b["severity"]) for b in sev_pick if len(descs[b["id"]]) >= 30]
    print(f"  ff_component: {len(comp_rows)}  per component: {per}", file=sys.stderr)
    print(f"  ff_severity: {len(sev_rows)}", file=sys.stderr)
    return comp_rows, sev_rows


def main():
    rng = random.Random(SEED)
    print("A issue_type ...", file=sys.stderr)
    a = task_issue_type(rng)
    print("B pr_merged ...", file=sys.stderr)
    b = task_pr_merged(rng)
    print("C/D firefox ...", file=sys.stderr)
    c, d = task_firefox(rng)
    rows = a + b + c + d
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    digest = hashlib.sha256(open(OUT, "rb").read()).hexdigest()
    open(OUT + ".sha256", "w").write(digest + "  dataset.jsonl\n")
    print(f"wrote {len(rows)} items -> {OUT}\nsha256 {digest}", file=sys.stderr)


if __name__ == "__main__":
    main()
