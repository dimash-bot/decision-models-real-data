"""v2 questions: 3 phrasings per task (P1 plain, P2 terse, P3 detailed). Same for every model.

Option descriptions come from the sources themselves where they exist:
  T3 - Bugzilla's own component descriptions (data/components.json, fetched by collect_v2.py)
  T4 - Mozilla's severity definitions (bugzilla.mozilla.org severity field docs), paraphrased minimally
  T5 - GitHub Advisory Database severity levels (CVSS v3 qualitative ranges)
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

FF_SEVERITY = [  # low -> high
    "S4: (Trivial) Bug has no impact on functionality, or is cosmetic (e.g. a typo or minor visual glitch).",
    "S3: (Normal) Blocks non-critical functionality, or a work around exists.",
    "S2: (Serious) Major functionality or product feature is broken or unusable, and there is no satisfactory work around.",
    "S1: (Catastrophic) Blocks development/testing, may impact more than 25% of users, causes data loss, likely to be a top crash, or a security issue.",
]
FF_SEV_LABELS = ["S4", "S3", "S2", "S1"]

ADV_SEVERITY = [  # low -> high (GitHub uses CVSS v3 qualitative ratings; "moderate" == API "medium")
    "low: CVSS 0.1-3.9. Limited impact, hard to exploit, or requires unlikely conditions.",
    "moderate: CVSS 4.0-6.9. Meaningful impact but exploitation needs user interaction, local access, or special conditions.",
    "high: CVSS 7.0-8.9. Serious impact such as significant data exposure or code execution under some preconditions.",
    "critical: CVSS 9.0-10.0. Easily exploitable remotely with severe impact, e.g. unauthenticated remote code execution or full compromise.",
]
ADV_LABELS = ["low", "medium", "high", "critical"]

ISSUE_CRIT = {
    "true": "Bug report: existing behavior is broken, wrong, crashes, or regressed.",
    "false": "Feature request: asks for new behavior, an option, or an enhancement to something that works as designed.",
}
PR_CRIT = {"true": "The pull request is merged.", "false": "The pull request is closed without being merged."}


def cwes():
    p = os.path.join(HERE, "data", "cwes.json")
    return json.load(open(p)) if os.path.exists(p) else {}


def components():
    p = os.path.join(HERE, "data", "components.json")
    return json.load(open(p)) if os.path.exists(p) else {}


def questions(task, variant):
    """Return the Decisions question object for task T1..T5 and phrasing P1..P3."""
    if task == "T1":
        ins = {
            "P1": "This is a newly filed GitHub issue. Is it a bug report (as opposed to a feature request)?",
            "P2": "Bug report?",
            "P3": "You are triaging a newly opened issue on a large open-source project. Decide whether the reporter is describing a defect in existing behavior (a bug) rather than asking for new functionality or an enhancement (a feature request).",
        }[variant]
        return {"type": "noul", "instructions": ins, "criteria": ISSUE_CRIT}
    if task == "T2":
        ins = {
            "P1": "This is a pull request as it looked when opened. Will the maintainers end up merging it?",
            "P2": "Will this PR be merged?",
            "P3": "You are a maintainer of this repository reviewing a pull request at the moment it was opened, seeing its title, description and size. Predict whether it will eventually be merged, or closed without merging.",
        }[variant]
        return {"type": "noul", "instructions": ins, "criteria": PR_CRIT}
    if task == "T3":
        ins = {
            "P1": "This is a newly filed Firefox bug. Which Firefox component does it belong to?",
            "P2": "Component?",
            "P3": "You are a Firefox bug triager. Using the component descriptions, assign this newly filed bug to the Bugzilla component whose team should own and fix it.",
        }[variant]
        return {"type": "choice", "instructions": ins, "criteria": components()}
    if task == "T4":
        ins = {
            "P1": "This is a newly filed Firefox bug. How severe is it, using Mozilla's severity scale?",
            "P2": "Severity?",
            "P3": "You are a Firefox triage owner. Rate this newly filed bug on Mozilla's severity scale, judging impact on users and functionality, not how urgent it is to fix.",
        }[variant]
        return {"type": "score", "instructions": ins, "criteria": FF_SEVERITY}
    if task == "T5":
        ins = {
            "P1": "This is a newly published security advisory. How severe is the vulnerability?",
            "P2": "Severity?",
            "P3": "You are a security analyst reviewing a newly published advisory for an open-source package. Rate the vulnerability's severity on the GitHub Advisory Database scale, considering impact and how easily it can be exploited.",
        }[variant]
        return {"type": "score", "instructions": ins, "criteria": ADV_SEVERITY}
    if task == "T6":
        ins = {
            "P1": "This is a newly published vulnerability (CVE) description. Which weakness type (CWE) is it?",
            "P2": "CWE?",
            "P3": "You are a vulnerability analyst mapping a newly published CVE to the Common Weakness Enumeration. Choose the CWE that best describes the root-cause weakness.",
        }[variant]
        return {"type": "choice", "instructions": ins, "criteria": cwes()}
    raise KeyError(task)


TASKS = ["T1", "T2", "T3", "T4", "T5", "T6"]
VARIANTS = ["P1", "P2", "P3"]
CLASSES = {  # class labels in index order, used by the scorer
    "T1": [False, True],
    "T2": [False, True],
    "T4": FF_SEV_LABELS,
    "T5": ADV_LABELS,
}
