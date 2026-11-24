---
name: slop-to-gold
description: Use when the user corrects an agent's code or repeats the same correction, complains about slop or recurring agent mistakes, asks to audit a codebase for anti-patterns agents might copy, or wants agent-written PRs trustworthy without line-by-line review.
---

# Slop to Gold

Agents copy whatever the codebase already shows them, so slop spreads like weeds. Make the codebase the strongest input, and make every correction permanent in code.

## Core rule

A correction becomes a **deterministic check first**: lint rule, type, test, dependency boundary, or an API that makes the mistake impossible. Prose (rules, AGENTS.md, comments) is the last resort, only when nothing deterministic fits.

Layer order, most trusted first: code design, lint/types/tests, verification, prose. Verification (running the app, tests) needs no special mode: do it, and report real output.

## Pick the mode

| Situation | Read |
|---|---|
| User corrected you, or the same mistake happened twice | `references/correction-to-check.md` |
| Asked to audit a repo, or starting on an unfamiliar one | `references/audit.md` |

Read only the one file that matches.

## Enforcement

A skill is advice and can be skipped. Enforcement lives in a PostToolUse hook that runs lint and typecheck after each edit. If the project has none, propose one; do not add it without asking.

## Done means

- The correction exists as a check that fails on the bad pattern, and you saw it fail.
- Old occurrences are listed or cleaned up.
- Any lint message you wrote tells the agent the root-cause fix, not just "don't".
