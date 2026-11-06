"""The one question per task. Every model gets exactly this wording - no per-model tuning."""

FF_COMPONENTS = {
    "Address Bar": "The URL bar / awesomebar: typing URLs, search suggestions, results dropdown, urlbar buttons.",
    "New Tab Page": "The new tab page (Firefox Home): top sites, stories, wallpapers, widgets on about:newtab / about:home.",
    "Messaging System": "In-product messages: onboarding screens, feature callouts, infobars, spotlight dialogs, CFR recommendations, message targeting/experiments.",
    "Sidebar": "The browser sidebar and vertical tabs panel: sidebar launcher, history/bookmarks/synced tabs/AI chatbot panels.",
    "Tabbed Browser": "Horizontal tabs and the tab strip: opening, closing, moving, grouping, pinning tabs, tab previews.",
    "PDF Viewer": "The built-in PDF.js viewer: rendering PDFs, forms, annotations, printing or saving PDFs.",
    "Session Restore": "Restoring windows/tabs after restart or crash, recently closed tabs/windows, session history saving.",
    "IP Protection": "The built-in VPN / IP protection feature: its toggle, panel, proxying, and status UI.",
}

FF_SEVERITY = [  # ordered low -> high (Mozilla's definitions, paraphrased)
    "S4: Trivial/cosmetic - does not affect functionality (e.g. a typo, minor visual glitch).",
    "S3: Blocks non-critical functionality, or a workaround exists.",
    "S2: Serious - major functionality or product feature is broken or unusable, with no satisfactory workaround.",
    "S1: Catastrophic - crash, data loss, security issue, or blocks development/testing for many users.",
]
SEV_INDEX = {"S4": 0, "S3": 1, "S2": 2, "S1": 3}

QUESTIONS = {
    "issue_type": {
        "type": "noul",
        "instructions": "This is a newly filed GitHub issue. Is it a bug report (as opposed to a feature request)?",
        "criteria": {
            "true": "Bug report: existing behavior is broken, wrong, crashes, or regressed.",
            "false": "Feature request: asks for new behavior, an option, or an enhancement to something that works as designed.",
        },
    },
    "pr_merged": {
        "type": "noul",
        "instructions": "This is a pull request as it looked when opened. Will the maintainers end up merging it?",
        "criteria": {
            "true": "The pull request is merged.",
            "false": "The pull request is closed without being merged.",
        },
    },
    "ff_component": {
        "type": "choice",
        "instructions": "This is a newly filed Firefox bug. Which Firefox component does it belong to?",
        "criteria": FF_COMPONENTS,
    },
    "ff_severity": {
        "type": "score",
        "instructions": "This is a newly filed Firefox bug. How severe is it, using Mozilla's severity scale?",
        "criteria": FF_SEVERITY,
    },
}
