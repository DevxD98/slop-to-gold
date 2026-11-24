#!/usr/bin/env python3
"""Turn evals/results/*.jsonl into a chart spec and a markdown summary, then draw the charts.

Run: python3 evals/make_charts.py
Writes evals/results/charts.json and evals/results/summary.md, then runs
evals/charts/render.mjs (rough.js, hand-drawn SVGs) into docs/ if its deps are installed:
  (cd evals/charts && npm install)
"""
import json
import os
import subprocess
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")

TRIGGER_LABELS = {
    "t-repeat-timer": "\"setTimeout again, told you last week\"",
    "t-recurring-effect": "\"agents keep writing useEffect\"",
    "t-audit": "\"audit for patterns agents copy\"",
    "t-trust-prs": "\"tired of reviewing every line\"",
    "t-third-time": "\"as any again, third time\"",
    "t-slop": "\"our agent code is full of slop\"",
    "n-dark-mode": "add a dark mode toggle",
    "n-python": "write a date parser in Python",
    "n-explain-effect": "explain useEffect cleanup",
    "n-setup-eslint": "set up ESLint (near miss)",
    "n-fix-test": "add a debounce option",
    "n-review-pr": "review a file for bugs (near miss)",
}
METRICS = [
    ("skill_loaded", "Skill loaded"),
    ("fixed_target", "Fixed the reported bug"),
    ("cleaned_old", "Fixed other copies too"),
    ("enforced", "Added a check that fails on it"),
    ("teaches_fix", "Check message names the fix"),
    ("verified_with_lint", "Ran lint to verify"),
    ("lint_clean_end", "Lint passes at the end"),
]
ARM_NAMES = {
    "invoked": "Skill invoked (/slop-to-gold)",
    "auto": "Skill loads on its own",
    "auto-v1": "Loads on its own (old description)",
    "without": "Skill blocked (baseline)",
}


def load(name):
    p = os.path.join(RES, name)
    return [r for r in (json.loads(l) for l in open(p) if l.strip()) if "error" not in r] if os.path.exists(p) else []


def frac(rows, key):
    vals = [r[key] for r in rows if r.get(key) is not None]
    hit = sum(bool(v) for v in vals)
    return {"v": hit / len(vals) if vals else 0, "txt": f"{hit}/{len(vals)}" if vals else "n/a"}


def trigger_rows(trig):
    by = defaultdict(list)
    for r in trig:
        by[(r["should"], r["id"])].append(r["fired"])
    return by


def main():
    charts, md = [], []
    t1, t2 = load("trigger.jsonl"), load("trigger-v2.jsonl")
    beh = load("behavior.jsonl")
    auto2 = [dict(r, arm="auto") for r in load("behavior-v2.jsonl")]

    # Trigger: old vs new description
    sets = [("Old description", trigger_rows(t1))] + ([("New description", trigger_rows(t2))] if t2 else [])
    rows = []
    for should, head in ((True, "Should load the skill"), (False, "Should not load the skill")):
        rows.append({"section": head})
        for cid in [c for (s, c) in sets[0][1] if s == should]:
            vals = []
            for _, by in sets:
                f = by.get((should, cid), [])
                vals.append({"v": sum(f) / len(f) if f else 0, "txt": f"{sum(f)}/{len(f)}"})
            rows.append({"label": TRIGGER_LABELS.get(cid, cid), "vals": vals})
    md.append("**Trigger evals** (2 runs per prompt)\n\n| Description | Recall (should load) | False triggers |\n|---|---|---|")
    for name, by in sets:
        tp = sum(sum(f) for (s, _), f in by.items() if s)
        pos = sum(len(f) for (s, _), f in by.items() if s)
        fp = sum(sum(f) for (s, _), f in by.items() if not s)
        neg = sum(len(f) for (s, _), f in by.items() if not s)
        md.append(f"| {name} | {tp}/{pos} | {fp}/{neg} |")
    charts.append({"file": "trigger.svg", "title": "When does the skill load on its own?",
                   "subtitle": "Share of runs that loaded the skill, before and after rewording the description.",
                   "series": [n for n, _ in sets], "rows": rows,
                   "note": "Headless claude -p, Sonnet, 2 runs per prompt, first 4 turns. Prompts in evals/cases.json."})

    # Behavior charts
    soft = [r for r in beh if r.get("variant") == "soft"]
    soft_arms = ["invoked", "auto", "without"]
    soft_rows = {a: [r for r in soft if r["arm"] == a] for a in soft_arms}
    if auto2:
        soft_rows = {"invoked": soft_rows["invoked"], "auto": auto2, "without": soft_rows["without"],
                     "auto-v1": soft_rows["auto"]}
    explicit = [r for r in beh if r.get("variant") == "explicit"]
    exp_rows = {a: [r for r in explicit if r["arm"] == a] for a in ("invoked", "without")}

    for key, title, groups in (
        ("behavior-soft.svg", "Plain correction: \"you did X again, fix it\"", soft_rows),
        ("behavior-explicit.svg", "Correction that also asks \"make sure it can't come back\"", exp_rows),
    ):
        charted = [a for a in groups if a != "auto-v1"]
        n_each = len(groups[charted[0]])
        charts.append({"file": key, "title": title,
                       "subtitle": f"Share of runs meeting each check. {n_each} runs per bar (4 scenarios x 2).",
                       "series": [ARM_NAMES[a] for a in charted],
                       "rows": [{"label": label, "vals": [frac(groups[a], k) for a in charted]} for k, label in METRICS],
                       "note": "Graded from files: a hidden probe file with the bad pattern is linted after each run."})
        md.append(f"\n**{title}**\n\n| Check | " + " | ".join(ARM_NAMES[a] for a in groups) + " |\n|---|" + "---|" * len(groups))
        for k, label in METRICS:
            md.append(f"| {label} | " + " | ".join(frac(groups[a], k)["txt"] for a in groups) + " |")
        md.append("\n| Arm | Avg cost | Avg turns | Runs adding prose rules | eslint-disable added |\n|---|---|---|---|---|")
        for a, rs in groups.items():
            costs = [r["cost"] for r in rs if r.get("cost")]
            turns = [r["turns"] for r in rs if r.get("turns")]
            md.append(f"| {ARM_NAMES[a]} | ${sum(costs) / max(len(costs), 1):.2f} | {sum(turns) / max(len(turns), 1):.1f} | "
                      f"{sum(bool(r.get('prose_added')) for r in rs)} | {sum(r.get('disables_added', 0) for r in rs)} |")

    json.dump(charts, open(os.path.join(RES, "charts.json"), "w"), indent=1)
    open(os.path.join(RES, "summary.md"), "w").write("\n".join(md) + "\n")
    print("\n".join(md))
    render = os.path.join(HERE, "charts", "render.mjs")
    if os.path.isdir(os.path.join(HERE, "charts", "node_modules")):
        subprocess.run(["node", render], check=True)
    else:
        print("\n(charts not drawn: run `cd evals/charts && npm install` first)")


if __name__ == "__main__":
    main()
