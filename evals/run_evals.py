#!/usr/bin/env python3
"""Run trigger and behavior evals for the slop-to-gold skill with headless Claude Code.

Each run is a fresh `claude -p` session in a copy of a fixture project. Hooks are
disabled and MCP servers are off so runs don't touch the host setup. The baseline
arm blocks only this skill (`--disallowedTools "Skill(slop-to-gold)"`); everything
else in the environment is the same.

Usage:
  python3 evals/run_evals.py trigger  --reps 2 --work <dir> --eslint-modules <node_modules>
  python3 evals/run_evals.py behavior --reps 2 --work <dir> --eslint-modules <node_modules>
  python3 evals/run_evals.py rival --rival self-improvement --rival-src <skill dir> --out rivals.jsonl ...

Results append to evals/results/<mode>.jsonl. Raw transcripts go to <work>/transcripts.
Grading is done from files and transcripts, never by asking a model.
"""
import argparse
import concurrent.futures as cf
import json
import os
import re
import shutil
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CASES = json.load(open(os.path.join(HERE, "cases.json")))
SKILL = "slop-to-gold"
BASE = ["claude", "-p", "--model", "sonnet", "--strict-mcp-config",
        "--settings", '{"disableAllHooks":true}', "--output-format", "stream-json", "--verbose"]
LINT_TOOLS = ["Bash(npm run lint*)", "Bash(npx eslint*)", "Bash(./node_modules/.bin/eslint*)",
              "Bash(node *)", "Bash(grep *)", "Bash(rg *)", "Bash(ls *)", "Bash(cat *)", "Bash(find *)"]
PROSE = ("AGENTS.md", "CLAUDE.md", ".cursorrules", "CONTRIBUTING.md", "README.md", "CONVENTIONS.md")
# Other skills to compare against. "src" is a folder passed with --rival-src (not vendored here);
# skills are copied into the run's .claude/skills, commands into .claude/commands. "slash" is
# what the user types to invoke it. A rival with no "src" is already installed globally.
RIVALS = {
    "self-improvement": {"kind": "skill", "slash": "/self-improvement", "arms": ("auto", "invoked")},
    "revise-claude-md": {"kind": "command", "slash": "/revise-claude-md", "arms": ("invoked",)},
    "receiving-code-review": {"kind": "global", "slash": "/superpowers:receiving-code-review", "arms": ("invoked",)},
}


def run_claude(prompt, cwd, extra, transcript):
    t0 = time.time()
    with open(transcript, "w") as out:
        # Prompt goes on stdin: --allowedTools/--disallowedTools are variadic and would eat a trailing argument.
        subprocess.run(BASE + extra, input=prompt, text=True, cwd=cwd, stdout=out,
                       stderr=subprocess.STDOUT, timeout=1200)
    return time.time() - t0, parse(transcript)


def parse(path):
    """Pull tool calls, skill loads, cost and final text out of a stream-json transcript."""
    calls, results, final = [], {}, {}
    for line in open(path, errors="ignore"):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if not isinstance(e, dict):
            continue
        msg = e.get("message")
        content = msg.get("content") if isinstance(msg, dict) else None
        if isinstance(content, list):
            for c in content:
                if not isinstance(c, dict):
                    continue
                if c.get("type") == "tool_use":
                    calls.append(c)
                elif c.get("type") == "tool_result":
                    results[c.get("tool_use_id")] = bool(c.get("is_error"))
        if e.get("type") == "result":
            final = e
    # Loaded via the Skill tool, or (for a /slop-to-gold slash invocation, which does not go
    # through the Skill tool) the run read one of the skill's own reference files.
    loaded = any(c["name"] == "Skill" and SKILL in json.dumps(c.get("input", {}))
                 and not results.get(c.get("id"), False) for c in calls) or any(
        c["name"] == "Read" and f"{SKILL}/references/" in c.get("input", {}).get("file_path", "") for c in calls)
    rival_loaded = {n: any((c["name"] == "Skill" and n in json.dumps(c.get("input", {})))
                           or (c["name"] == "Read" and f"skills/{n}/" in c.get("input", {}).get("file_path", ""))
                           for c in calls) for n in RIVALS}
    attempted = any(c["name"] == "Skill" and SKILL in json.dumps(c.get("input", {})) for c in calls)
    bash = [c["input"].get("command", "") for c in calls if c["name"] == "Bash"]
    return {"skill_loaded": loaded, "skill_attempted": attempted, "rival_loaded": rival_loaded, "bash": bash,
            "cost": final.get("total_cost_usd"), "turns": final.get("num_turns"),
            "final": final.get("result") or ""}


def fresh_copy(fixture, work, run_id, modules):
    dst = os.path.join(work, "runs", run_id)
    shutil.copytree(os.path.join(HERE, "fixtures", fixture), dst)
    os.symlink(modules, os.path.join(dst, "node_modules"))
    return dst


def eslint(cwd, modules, *args):
    p = subprocess.run([os.path.join(modules, ".bin", "eslint"), "--format", "json", *args],
                       cwd=cwd, capture_output=True, text=True)
    try:
        return p.returncode, json.loads(p.stdout or "[]")
    except ValueError:
        return p.returncode, None  # config crashed


def read(path):
    try:
        return open(path, errors="ignore").read()
    except OSError:
        return ""


def grade(case, d, modules, info, before):
    bad = re.compile(case["bad"])
    g = {}
    g["fixed_target"] = not bad.search(read(os.path.join(d, case["target"])))
    g["cleaned_old"] = all(not bad.search(read(os.path.join(d, f))) for f in case["old"])

    rc, rep = eslint(d, modules, "src")
    g["lint_clean_end"] = rc == 0 and rep is not None
    g["config_ok"] = rep is not None

    if case["legit"]:
        f, rx = case["legit"]
        g["legit_kept"] = bool(re.search(rx, read(os.path.join(d, f))))
    else:
        g["legit_kept"] = None

    probe_path, probe_src = case["probe"]
    os.makedirs(os.path.dirname(os.path.join(d, probe_path)), exist_ok=True)
    open(os.path.join(d, probe_path), "w").write(probe_src)
    rc, rep = eslint(d, modules, probe_path)
    msgs = [m for f in (rep or []) for m in f.get("messages", []) if m.get("severity") == 2]
    g["enforced"] = bool(msgs)
    text = " ".join(m.get("message", "") for m in msgs).lower()
    g["teaches_fix"] = g["enforced"] and any(k.lower() in text for k in case["teach"])
    g["probe_message"] = text[:300]

    g["verified_with_lint"] = any(re.search(r"\beslint\b|npm run lint", b) for b in info["bash"])
    after = snapshot(d)
    g["prose_added"] = any(n in after and after[n] != before.get(n) for n in PROSE) or any(
        n.startswith(".learnings/") or n == ".claude.local.md" for n in after if after[n] != before.get(n))
    g["prose_only"] = g["prose_added"] and not g["enforced"]
    src_text = "".join(read(os.path.join(d, p)) for p in after if p.startswith("src/"))
    g["disables_added"] = len(re.findall(r"eslint-disable", src_text))
    g["hook_added"] = os.path.exists(os.path.join(d, ".claude", "settings.json"))
    g["hook_mentioned"] = "hook" in info["final"].lower()
    return g


def snapshot(d):
    out = {}
    for dp, dns, fns in os.walk(d):
        dns[:] = [x for x in dns if x != "node_modules"]
        for fn in fns:
            rel = os.path.relpath(os.path.join(dp, fn), d)
            out[rel] = read(os.path.join(dp, fn))
    return out


def trigger_job(case, rep, args):
    rid = f"trig-{case['id']}-r{rep}"
    d = fresh_copy("timer", args.work, rid, args.eslint_modules)
    secs, info = run_claude(case["prompt"], d, ["--max-turns", "4", "--max-budget-usd", "1"],
                            os.path.join(args.work, "transcripts", rid + ".jsonl"))
    return {"id": case["id"], "rep": rep, "should": case["should"], "fired": info["skill_loaded"],
            "cost": info["cost"], "secs": round(secs, 1)}


def behavior_job(case, variant, arm, rep, args):
    rid = f"beh-{case['id']}-{variant}-{arm}-r{rep}"
    d = fresh_copy(case["id"], args.work, rid, args.eslint_modules)
    before = snapshot(d)
    extra = ["--permission-mode", "acceptEdits", "--max-turns", "40", "--max-budget-usd", "3",
             "--allowedTools", *LINT_TOOLS]
    prompt = case[variant]
    if arm == "without":
        extra += ["--disallowedTools", f"Skill({SKILL})"]
    elif arm == "invoked":
        prompt = f"/{SKILL} {prompt}"
    secs, info = run_claude(prompt, d, extra, os.path.join(args.work, "transcripts", rid + ".jsonl"))
    g = grade(case, d, args.eslint_modules, info, before)
    return {"id": case["id"], "variant": variant, "arm": arm, "rep": rep, "skill_loaded": info["skill_loaded"],
            "cost": info["cost"], "turns": info["turns"], "secs": round(secs, 1), **g}


def rival_job(case, name, arm, rep, args):
    """Same soft correction, with slop-to-gold blocked and a rival skill present instead."""
    rv = RIVALS[name]
    rid = f"riv-{name}-{case['id']}-{arm}-r{rep}"
    d = fresh_copy(case["id"], args.work, rid, args.eslint_modules)
    if rv["kind"] == "skill":
        shutil.copytree(args.rival_src, os.path.join(d, ".claude", "skills", name))
    elif rv["kind"] == "command":
        os.makedirs(os.path.join(d, ".claude", "commands"), exist_ok=True)
        shutil.copy(args.rival_src, os.path.join(d, ".claude", "commands", name + ".md"))
    before = snapshot(d)
    extra = ["--permission-mode", "acceptEdits", "--max-turns", "40", "--max-budget-usd", "3",
             "--allowedTools", *LINT_TOOLS, "--disallowedTools", f"Skill({SKILL})"]
    prompt = case["soft"] if arm == "auto" else f"{rv['slash']} {case['soft']}"
    secs, info = run_claude(prompt, d, extra, os.path.join(args.work, "transcripts", rid + ".jsonl"))
    # Invoked arms load it by construction; for auto, look for a Skill call or a read of its files.
    used = arm == "invoked" or info["rival_loaded"].get(name, False)
    g = grade(case, d, args.eslint_modules, info, before)
    return {"id": case["id"], "variant": "soft", "arm": f"{name}:{arm}", "rep": rep, "rival_used": used,
            "cost": info["cost"], "turns": info["turns"], "secs": round(secs, 1), **g}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["trigger", "behavior", "rival"])
    ap.add_argument("--rival", default="", help="rival: which entry of RIVALS")
    ap.add_argument("--rival-src", default="", help="rival: path to the rival skill folder or command file")
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--work", required=True)
    ap.add_argument("--eslint-modules", required=True)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--only", default="")
    ap.add_argument("--variant", default="", help="behavior: only this prompt variant (soft|explicit)")
    ap.add_argument("--arm", default="", help="behavior: only this arm (auto|invoked|without)")
    ap.add_argument("--out", default="", help="results file name (default: <mode>.jsonl)")
    args = ap.parse_args()
    args.eslint_modules = os.path.abspath(args.eslint_modules)
    os.makedirs(os.path.join(args.work, "transcripts"), exist_ok=True)
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    out = os.path.join(HERE, "results", args.out or f"{args.mode}.jsonl")

    jobs = []
    if args.mode == "rival":
        for c in CASES["behavior"]:
            for arm in RIVALS[args.rival]["arms"]:
                for r in range(args.reps):
                    jobs.append((rival_job, (c, args.rival, arm, r, args)))
    elif args.mode == "trigger":
        for c in CASES["trigger"]:
            for r in range(args.reps):
                jobs.append((trigger_job, (c, r, args)))
    else:
        for c in CASES["behavior"]:
            if args.only and c["id"] != args.only:
                continue
            # soft = a plain correction; explicit = also asks to make it stick.
            for variant, arms in (("soft", ("auto", "invoked", "without")), ("explicit", ("invoked", "without"))):
                if args.variant and variant != args.variant:
                    continue
                for arm in arms:
                    if args.arm and arm != args.arm:
                        continue
                    for r in range(args.reps):
                        jobs.append((behavior_job, (c, variant, arm, r, args)))

    with cf.ThreadPoolExecutor(args.jobs) as ex, open(out, "a") as f:
        futs = {ex.submit(fn, *a): a for fn, a in jobs}
        for fut in cf.as_completed(futs):
            try:
                row = fut.result()
            except Exception as e:  # keep going; record the failure
                row = {"error": repr(e), "args": str(futs[fut][0].get("id"))}
            f.write(json.dumps(row) + "\n")
            f.flush()
            print(json.dumps(row)[:200], flush=True)


if __name__ == "__main__":
    main()
