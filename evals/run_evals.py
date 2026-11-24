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


EXTRA_PATH = []  # --bin dirs (e.g. a venv with ruff) prepended to PATH for runs and probes


def env():
    e = dict(os.environ)
    if EXTRA_PATH:
        e["PATH"] = os.pathsep.join(EXTRA_PATH + [e.get("PATH", "")])
    return e


def run_claude(prompt, cwd, extra, transcript):
    t0 = time.time()
    with open(transcript, "w") as out:
        # Prompt goes on stdin: --allowedTools/--disallowedTools are variadic and would eat a trailing argument.
        subprocess.run(BASE + extra, input=prompt, text=True, cwd=cwd, stdout=out,
                       stderr=subprocess.STDOUT, timeout=1200, env=env())
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


# Clean mode: every arm runs with --setting-sources project,local, so none of the user's own
# skills or plugins are present. The skill under test (if any) is copied into the project.
CLEAN = ["--setting-sources", "project,local"]
CLEAN_ARMS = [("slop-to-gold", "auto"), ("slop-to-gold", "invoked"), ("none", "-"),
              ("self-improvement", "auto"), ("self-improvement", "invoked"),
              ("revise-claude-md", "invoked"), ("receiving-code-review", "invoked")]


def install(name, src, d):
    """Copy a skill folder (or a command file) into the run's project .claude/."""
    if src.endswith(".md"):
        os.makedirs(os.path.join(d, ".claude", "commands"), exist_ok=True)
        shutil.copy(src, os.path.join(d, ".claude", "commands", name + ".md"))
    else:
        dst = os.path.join(d, ".claude", "skills", name)
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns(
            ".git", ".github", "evals", "tests", "docs", "node_modules", ".claude-plugin", "*.png", "README.md"))


def loaded_from(transcript, name):
    for line in open(transcript, errors="ignore"):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        msg = e.get("message") if isinstance(e, dict) else None
        for c in (msg.get("content") if isinstance(msg, dict) and isinstance(msg.get("content"), list) else []):
            if isinstance(c, dict) and c.get("type") == "tool_use":
                i = json.dumps(c.get("input", {}))
                if (c["name"] == "Skill" and name in i) or (c["name"] == "Read" and f"skills/{name}/" in i):
                    return True
    return False


def clean_job(case, name, arm, rep, args):
    rid = f"cln-{name}-{case['id']}-{arm}-{args.variant or 'soft'}-r{rep}"
    d = fresh_copy(case["id"], args.work, rid, args.eslint_modules)
    if name != "none":
        install(name, args.src[name], d)
    before = snapshot(d)
    extra = CLEAN + ["--permission-mode", "acceptEdits", "--max-turns", "40", "--max-budget-usd", "3",
                     "--allowedTools", *LINT_TOOLS]
    variant = args.variant or "soft"
    prompt = f"/{name} {case[variant]}" if arm == "invoked" else case[variant]
    tpath = os.path.join(args.work, "transcripts", rid + ".jsonl")
    secs, info = run_claude(prompt, d, extra, tpath)
    g = grade(case, d, args.eslint_modules, info, before)
    used = None if name == "none" else (arm == "invoked" or loaded_from(tpath, name))
    return {"id": case["id"], "variant": variant, "arm": f"{name}:{arm}", "rep": rep, "skill_used": used,
            "cost": info["cost"], "turns": info["turns"], "secs": round(secs, 1), **g}


def clean_trigger_job(case, rep, args):
    rid = f"clt-{case['id']}-r{rep}"
    d = fresh_copy("timer", args.work, rid, args.eslint_modules)
    install(SKILL, args.src[SKILL], d)
    tpath = os.path.join(args.work, "transcripts", rid + ".jsonl")
    secs, info = run_claude(case["prompt"], d, CLEAN + ["--max-turns", "4", "--max-budget-usd", "1"], tpath)
    return {"id": case["id"], "rep": rep, "should": case["should"], "fired": loaded_from(tpath, SKILL),
            "cost": info["cost"], "secs": round(secs, 1)}


# ---- Audit mode and other-language scenarios (clean setup: only the skill under test is present) ----
LANG_TOOLS = LINT_TOOLS + ["Bash(ruff *)", "Bash(python3 *)", "Bash(python *)", "Bash(pytest *)", "Bash(npx *)",
                           "Bash(npm *)", "Bash(tsc *)", "Bash(node *)"]
AUDIT_TOOLS = ["Bash(python3 *)", "Bash(python *)", "Bash(grep *)", "Bash(rg *)", "Bash(ls *)", "Bash(cat *)",
               "Bash(find *)", "Bash(wc *)", "Bash(head *)", "Bash(npm *)", "Bash(node *)"]
CHECK_RE = re.compile(r"eslint|lint rule|no-restricted|ast-grep|semgrep|ruff|dependency-cruiser|import-linter|"
                      r"typecheck|type check|tsc\b|unit test|regression test|ci check|codemod|lint check", re.I)
GAP_RE = re.compile(r"(no|missing|without|lacks?|doesn.t (have|run)|not (set up|configured|present))[^.\n]{0,50}"
                    r"(lint|eslint|test|typecheck|tsc)", re.I)


def sh(cmd, d):
    p = subprocess.run(cmd, shell=True, cwd=d, capture_output=True, text=True, env=env(), timeout=300)
    return p.returncode, (p.stdout + p.stderr)


def put(d, spec):
    path, src = spec
    os.makedirs(os.path.dirname(os.path.join(d, path)), exist_ok=True)
    open(os.path.join(d, path), "w").write(src)


def fresh(fixture, work, rid, modules):
    dst = os.path.join(work, "runs", rid)
    shutil.copytree(os.path.join(HERE, "fixtures", fixture), dst)
    if modules:
        os.symlink(modules, os.path.join(dst, "node_modules"))
    return dst


def grade_lang(case, d, info, before):
    g = {}
    if case.get("fixed_cmd"):
        rc, _ = sh(case["fixed_cmd"], d)
        g["fixed_target"] = g["cleaned_old"] = rc == 0
    else:
        bad = re.compile(case["bad"])
        g["fixed_target"] = not bad.search(read(os.path.join(d, case["target"])))
        g["cleaned_old"] = all(not bad.search(read(os.path.join(d, f))) for f in case["old"])
    g["legit_kept"] = bool(re.search(case["legit"][1], read(os.path.join(d, case["legit"][0])))) if case["legit"] else None
    rc, _ = sh(case["end_cmd"], d)
    g["lint_clean_end"] = rc == 0
    # Probe. Test scenarios: tests must exist and pass on the fixed code, then fail on the buggy code.
    # Lint scenarios: a clean probe must pass (the check works), then the bad probe must fail.
    if case["kind"] == "test":
        rc, out = sh(case["probe_cmd"], d)
        m = re.search(r"# tests (\d+)", out)
        ok = rc == 0 and m and int(m.group(1)) > 0
    else:
        put(d, case["probe_ok"])
        rc, out = sh(case["probe_cmd"], d)
        ok = rc == 0
    g["config_ok"] = bool(ok)
    put(d, case["probe"])
    rc, out = sh(case["probe_cmd"], d)
    g["enforced"] = bool(ok) and rc != 0
    text = out.lower()
    g["teaches_fix"] = (g["enforced"] and any(k.lower() in text for k in case["teach"])) if case["teach"] else None
    g["probe_message"] = text[:300]
    g["verified_with_lint"] = any(re.search(case["verify_re"], b) for b in info["bash"])
    after = snapshot(d)
    g["prose_added"] = any(n in after and after[n] != before.get(n) for n in PROSE) or any(
        n.startswith(".learnings/") or n == ".claude.local.md" for n in after if after[n] != before.get(n))
    g["prose_only"] = g["prose_added"] and not g["enforced"]
    src_text = "".join(read(os.path.join(d, p)) for p in after if p.startswith("src/") and p != case["probe"][0])
    g["disables_added"] = len(re.findall(r"eslint-disable|noqa|ts-ignore|ts-expect-error", src_text))
    g["hook_added"] = os.path.exists(os.path.join(d, ".claude", "settings.json"))
    g["hook_mentioned"] = "hook" in info["final"].lower()
    return g


def lang_job(case, name, arm, rep, args):
    rid = f"lng-{name}-{case['id']}-{arm}-r{rep}"
    d = fresh(case["id"], args.work, rid, args.ts_modules if case["tools"] == "ts" else args.eslint_modules)
    if name != "none":
        install(name, args.src[name], d)
    before = snapshot(d)
    extra = CLEAN + ["--permission-mode", "acceptEdits", "--max-turns", "40", "--max-budget-usd", "3",
                     "--allowedTools", *LANG_TOOLS]
    variant = args.variant or "soft"
    prompt = f"/{name} {case[variant]}" if arm == "invoked" else case[variant]
    tpath = os.path.join(args.work, "transcripts", rid + ".jsonl")
    secs, info = run_claude(prompt, d, extra, tpath)
    g = grade_lang(case, d, info, before)
    used = None if name == "none" else (arm == "invoked" or loaded_from(tpath, name))
    return {"id": case["id"], "variant": variant, "arm": f"{name}:{arm}", "rep": rep, "skill_used": used,
            "cost": info["cost"], "turns": info["turns"], "secs": round(secs, 1), **g}


def audit_job(case, name, arm, rep, args):
    rid = f"aud-{name}-{case['id']}-{arm}-r{rep}"
    d = fresh(case["fixture"], args.work, rid, None)
    if name != "none":
        install(name, args.src[name], d)
    before = snapshot(d)
    extra = CLEAN + ["--permission-mode", "acceptEdits", "--max-turns", "40", "--max-budget-usd", "3",
                     "--allowedTools", *AUDIT_TOOLS]
    prompt = CASES["audit_prompt"]
    if arm == "invoked":
        prompt = f"/{name} {prompt}"
    tpath = os.path.join(args.work, "transcripts", rid + ".jsonl")
    secs, info = run_claude(prompt, d, extra, tpath)
    after = snapshot(d)
    changed = [f for f in before if after.get(f) != before[f]]
    added = [f for f in after if f not in before and not f.endswith(".md") and not f.startswith(".claude/")]
    final = info["final"]
    low = final.lower()
    hits = [any(k.lower() in low for k in grp) for grp in case["patterns"]]
    used = None if name == "none" else (arm == "invoked" or loaded_from(tpath, name))
    return {"id": case["id"], "variant": "audit", "arm": f"{name}:{arm}", "rep": rep, "skill_used": used,
            "source_unchanged": not changed and not added, "changed_files": (changed + added)[:5],
            "names_patterns": all(hits), "patterns_named": sum(hits),
            "proposes_check": bool(CHECK_RE.search(final)), "notes_infra_gap": bool(GAP_RE.search(final)),
            "ran_scan": any("scan.py" in b for b in info["bash"]), "final_len": len(final),
            "cost": info["cost"], "turns": info["turns"], "secs": round(secs, 1)}


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
    ap.add_argument("mode", choices=["trigger", "behavior", "rival", "clean", "clean-trigger", "audit", "lang"])
    ap.add_argument("--src", action="append", default=[], help="clean: name=path of a skill folder or command file")
    ap.add_argument("--rival", default="", help="rival: which entry of RIVALS")
    ap.add_argument("--rival-src", default="", help="rival: path to the rival skill folder or command file")
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--work", required=True)
    ap.add_argument("--eslint-modules", required=True)
    ap.add_argument("--ts-modules", default="", help="lang: node_modules with typescript + typescript-eslint")
    ap.add_argument("--bin", action="append", default=[], help="dir prepended to PATH (e.g. a venv bin with ruff)")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--only", default="")
    ap.add_argument("--variant", default="", help="behavior: only this prompt variant (soft|explicit)")
    ap.add_argument("--arm", default="", help="behavior: only this arm (auto|invoked|without)")
    ap.add_argument("--out", default="", help="results file name (default: <mode>.jsonl)")
    args = ap.parse_args()
    args.eslint_modules = os.path.abspath(args.eslint_modules)
    args.ts_modules = os.path.abspath(args.ts_modules) if args.ts_modules else ""
    EXTRA_PATH.extend(os.path.abspath(b) for b in args.bin)
    args.src = dict(x.split("=", 1) for x in args.src)
    args.src.setdefault(SKILL, os.path.dirname(HERE))
    os.makedirs(os.path.join(args.work, "transcripts"), exist_ok=True)
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    out = os.path.join(HERE, "results", args.out or f"{args.mode}.jsonl")

    jobs = []
    if args.mode == "clean":
        for c in CASES["behavior"]:
            if args.only and c["id"] != args.only:
                continue
            for name, arm in CLEAN_ARMS:
                if (args.arm and f"{name}:{arm}" != args.arm) or (name != "none" and name not in args.src):
                    continue
                for r in range(args.reps):
                    jobs.append((clean_job, (c, name, arm, r, args)))
    elif args.mode in ("audit", "lang"):
        key, fn = ("audit", audit_job) if args.mode == "audit" else ("lang", lang_job)
        for c in CASES[key]:
            if args.only and c["id"] != args.only:
                continue
            for name, arm in CLEAN_ARMS:
                if (args.arm and f"{name}:{arm}" != args.arm) or (name != "none" and name not in args.src):
                    continue
                for r in range(args.reps):
                    jobs.append((fn, (c, name, arm, r, args)))
    elif args.mode == "clean-trigger":
        for c in CASES["trigger"] + CASES["trigger_heldout"]:
            for r in range(args.reps):
                jobs.append((clean_trigger_job, (c, r, args)))
    elif args.mode == "rival":
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
