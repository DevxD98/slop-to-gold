# slop-to-gold

A single [Claude Code skill](https://docs.claude.com/en/docs/claude-code/skills) that turns agent corrections into permanent, deterministic checks instead of prose rules.

Agents copy whatever the codebase already shows them, so slop spreads. This skill makes the codebase the strongest input: when you correct an agent, the fix becomes a lint rule, type, test or dependency boundary first. Prose (AGENTS.md, comments) is the last resort.

Based on ideas from the talk ["slop into gold"](https://youtu.be/O_zcc6Xl12g). The talk is the source of the thesis; this repo is an independent adaptation.

## What it does

| Mode | Triggers when | Does |
|---|---|---|
| Correction to check | You correct the agent, or the same mistake happens twice | Picks the strongest check, writes a lint message that teaches the root-cause fix, proves the check fails on the bad pattern, offers to clean up old occurrences |
| Audit | You ask to audit a repo, or start on an unfamiliar one | Runs `scripts/scan.py` for anti-pattern counts, then proposes a ranked list of checks. It changes nothing until you pick |

## Install

```bash
git clone https://github.com/DevxD98/-slop-to-gold.git ~/.claude/skills/slop-to-gold
```

Note: the repo name starts with a hyphen. If a command treats the URL or folder as a flag, put `--` before it or clone into the explicit path as above.

Requires `python3` for the scan. The optional hook also needs `bash`, `jq` and `npm`.

## Optional: enforcement hook

A skill is advice and can be skipped. The hook enforces it by running the project's own `lint` and `typecheck` scripts after every edit, and feeding failures back to Claude (exit code 2).

Add to `~/.claude/settings.json`, merging into your existing `hooks.PostToolUse` array:

```json
{
  "matcher": "Edit|Write|MultiEdit",
  "hooks": [
    {
      "type": "command",
      "command": "bash \"$HOME/.claude/skills/slop-to-gold/scripts/post-edit-check.sh\"",
      "timeout": 90,
      "statusMessage": "Checking lint/typecheck..."
    }
  ]
}
```

It stays silent unless all of these hold: the edited file is JS/TS, a `package.json` exists above it, `node_modules` is installed, and `package.json` defines a `lint` and/or `typecheck` script.

**Cost:** it runs the whole project lint after every edit (60s cap per script), which can be slow on large repos. To disable it, delete the entry.

## Status

Early. Tested with subagents (baseline vs. with-skill runs, trigger tests, and a live hook fire in a throwaway project), not yet across many real repos. Issues and findings welcome.

## License

MIT
