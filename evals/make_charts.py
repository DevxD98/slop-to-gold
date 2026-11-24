#!/usr/bin/env python3
"""Build README charts (SVG, light + dark) and a markdown summary from evals/results/*.

Run: python3 evals/make_charts.py
Writes docs/trigger.svg, docs/behavior-soft.svg, docs/behavior-explicit.svg, evals/results/summary.md
"""
import json
import os
from collections import defaultdict
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(os.path.dirname(HERE), "docs")
RES = os.path.join(HERE, "results")

# Reference palette (validated light + dark with the dataviz validator; slots 1-3 in fixed order).
SERIES = [("#2a78d6", "#3987e5"), ("#eb6834", "#d95926"), ("#1baf7a", "#199e70")]
W, LABEL_W, BAR_H, GAP, PAD = 800, 290, 14, 2, 24


def load(name):
    p = os.path.join(RES, name)
    return [json.loads(l) for l in open(p) if l.strip()] if os.path.exists(p) else []


def bar_path(x, y, w, h, r=4):
    """Bar anchored at x with a rounded data end only."""
    if w <= 0:
        return ""
    r = min(r, w, h / 2)
    return (f"M{x},{y}H{x + w - r}Q{x + w},{y} {x + w},{y + r}V{y + h - r}"
            f"Q{x + w},{y + h} {x + w - r},{y + h}H{x}Z")


def chart(path, title, subtitle, rows, series_names, note):
    """rows: list of ("section", text) or (label, [(value 0..1, text), ...])."""
    n = len(series_names)
    plot_x, plot_w = LABEL_W, W - LABEL_W - 70
    y = 86 if n > 1 else 66
    body = []
    for row in rows:
        if row[0] == "section":
            y += 8
            body.append(f'<text x="{PAD}" y="{y + 10}" class="t2 b">{escape(row[1])}</text>')
            y += 22
            continue
        label, vals = row
        group_h = n * BAR_H + (n - 1) * GAP
        body.append(f'<text x="{LABEL_W - 12}" y="{y + group_h / 2 + 4}" class="t1" text-anchor="end">{escape(label)}</text>')
        for i, (v, txt) in enumerate(vals):
            by = y + i * (BAR_H + GAP)
            w = round(plot_w * v, 1)
            body.append(f'<path d="{bar_path(plot_x, by, w, BAR_H)}" class="s{i + 1}"><title>{escape(series_names[i])}: {escape(txt)}</title></path>')
            body.append(f'<text x="{plot_x + w + 6}" y="{by + BAR_H - 3}" class="t2 v">{escape(txt)}</text>')
        y += group_h + 12
    height = y + 34
    grid = "".join(
        f'<line x1="{plot_x + plot_w * f}" x2="{plot_x + plot_w * f}" y1="{70 if n > 1 else 52}" y2="{y - 6}" class="g"/>'
        f'<text x="{plot_x + plot_w * f}" y="{y + 8}" class="t3" text-anchor="middle">{int(f * 100)}%</text>'
        for f in (0, 0.5, 1))
    legend = ""
    if n > 1:
        lx = PAD
        for i, name in enumerate(series_names):
            legend += f'<rect x="{lx}" y="54" width="12" height="12" rx="3" class="s{i + 1}"/><text x="{lx + 18}" y="64" class="t2">{escape(name)}</text>'
            lx += 30 + 7.2 * len(name)
    css = ["svg{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif}",
           ".bg{fill:#fcfcfb}.t1{fill:#0b0b0b;font-size:13px}.t2{fill:#52514e;font-size:12px}.t3{fill:#6f6e69;font-size:11px}",
           ".h{fill:#0b0b0b;font-size:16px;font-weight:600}.b{font-weight:600}.v{font-variant-numeric:tabular-nums}.g{stroke:#e4e3df;stroke-width:1}"]
    css += [f".s{i + 1}{{fill:{lt}}}" for i, (lt, _) in enumerate(SERIES[:n])]
    dark = [".bg{fill:#1a1a19}.t1,.h{fill:#f0efec}.t2{fill:#c3c2b7}.t3{fill:#9b9a92}.g{stroke:#383835}"]
    dark += [f".s{i + 1}{{fill:{dk}}}" for i, (_, dk) in enumerate(SERIES[:n])]
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" viewBox="0 0 {W} {height}" role="img" aria-label="{escape(title)}">'
           f'<style>{"".join(css)}@media (prefers-color-scheme: dark){{{"".join(dark)}}}</style>'
           f'<rect width="100%" height="100%" rx="8" class="bg"/>'
           f'<text x="{PAD}" y="28" class="h">{escape(title)}</text>'
           f'<text x="{PAD}" y="46" class="t2">{escape(subtitle)}</text>'
           f'{legend}{grid}{"".join(body)}'
           f'<text x="{PAD}" y="{height - 10}" class="t3">{escape(note)}</text></svg>')
    os.makedirs(DOCS, exist_ok=True)
    open(path, "w").write(svg)


def frac(rows, key):
    vals = [r[key] for r in rows if r.get(key) is not None]
    return (sum(bool(v) for v in vals) / len(vals), f"{sum(bool(v) for v in vals)}/{len(vals)}") if vals else (0, "n/a")


METRICS = [
    ("fixed_target", "Fixed the reported bug"),
    ("cleaned_old", "Fixed other copies too"),
    ("enforced", "Added a check that fails on it"),
    ("teaches_fix", "Check message names the fix"),
    ("verified_with_lint", "Ran lint to verify"),
    ("lint_clean_end", "Lint passes at the end"),
]
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
ARM_NAMES = {"invoked": "Skill invoked (/slop-to-gold)", "auto": "Skill available (auto)", "without": "Skill blocked (baseline)"}


def main():
    trig = load("trigger.jsonl")
    beh = [r for r in load("behavior.jsonl") if "error" not in r]
    md = []

    # Trigger chart
    by = defaultdict(list)
    for r in trig:
        by[(r["should"], r["id"])].append(r["fired"])
    rows = []
    for should, head in ((True, "Should load the skill"), (False, "Should not load the skill")):
        rows.append(("section", head))
        for (s, cid), fired in by.items():
            if s == should:
                rows.append((TRIGGER_LABELS.get(cid, cid), [(sum(fired) / len(fired), f"{sum(fired)}/{len(fired)}")]))
    tp = sum(sum(f) for (s, _), f in by.items() if s)
    pos = sum(len(f) for (s, _), f in by.items() if s)
    fp = sum(sum(f) for (s, _), f in by.items() if not s)
    neg = sum(len(f) for (s, _), f in by.items() if not s)
    chart(os.path.join(DOCS, "trigger.svg"), "When does the skill load on its own?",
          f"Share of runs that loaded the skill. Recall {tp}/{pos}, false triggers {fp}/{neg}.",
          rows, ["Loaded the skill"], "Headless claude -p, Sonnet, 2 runs per prompt, first 4 turns. Prompts in evals/cases.json.")
    md.append(f"**Trigger:** recall {tp}/{pos} ({100 * tp / max(pos, 1):.0f}%), false triggers {fp}/{neg}.\n")

    # Behavior charts
    for variant, arms, fname, title in (
        ("soft", ["invoked", "auto", "without"], "behavior-soft.svg", "Plain correction: \"you did X again, fix it\""),
        ("explicit", ["invoked", "without"], "behavior-explicit.svg", "Correction that also asks \"make sure it can't come back\""),
    ):
        sub = [r for r in beh if r.get("variant") == variant]
        if not sub:
            continue
        rows = [(label, [frac([r for r in sub if r["arm"] == a], k) for a in arms]) for k, label in METRICS]
        n_each = len([r for r in sub if r["arm"] == arms[0]])
        chart(os.path.join(DOCS, fname), title,
              f"Share of runs meeting each check. {n_each} runs per arm (4 scenarios x 2).",
              rows, [ARM_NAMES[a] for a in arms],
              "Graded from files: a hidden probe file with the bad pattern is linted after each run.")
        md.append(f"\n**{title}**\n\n| Check | " + " | ".join(ARM_NAMES[a] for a in arms) + " |\n|---|" + "---|" * len(arms))
        for k, label in METRICS:
            md.append(f"| {label} | " + " | ".join(frac([r for r in sub if r["arm"] == a], k)[1] for a in arms) + " |")
        extra = []
        for a in arms:
            rs = [r for r in sub if r["arm"] == a]
            costs = [r["cost"] for r in rs if r.get("cost")]
            turns = [r["turns"] for r in rs if r.get("turns")]
            loaded = sum(bool(r.get("skill_loaded")) for r in rs)
            prose = sum(bool(r.get("prose_added")) for r in rs)
            dis = sum(r.get("disables_added", 0) for r in rs)
            extra.append(f"| {ARM_NAMES[a]} | {loaded}/{len(rs)} | ${sum(costs) / max(len(costs), 1):.2f} | "
                         f"{sum(turns) / max(len(turns), 1):.1f} | {prose} | {dis} |")
        md.append("\n| Arm | Skill loaded | Avg cost | Avg turns | Runs adding prose rules | eslint-disable added |\n|---|---|---|---|---|---|")
        md += extra
    open(os.path.join(RES, "summary.md"), "w").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
