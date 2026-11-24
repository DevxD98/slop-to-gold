**Trigger evals** (2 runs per prompt)

| Description | Recall (should load) | False triggers |
|---|---|---|
| Old description | 10/12 | 0/12 |
| New description | 12/12 | 0/12 |

**Plain correction: "you did X again, fix it"**

| Check | Skill invoked (/slop-to-gold) | Skill loads on its own | No skill installed (baseline) |
|---|---|---|---|
| Skill loaded | 8/8 | 8/8 | n/a |
| Fixed the reported bug | 8/8 | 8/8 | 8/8 |
| Fixed other copies too | 8/8 | 8/8 | 2/8 |
| Added a check that fails on it | 8/8 | 8/8 | 0/8 |
| Check message names the fix | 8/8 | 8/8 | 0/8 |
| Ran lint to verify | 8/8 | 8/8 | 0/8 |
| Lint passes at the end | 8/8 | 8/8 | 8/8 |

| Arm | Avg cost | Avg turns | Runs adding prose rules | eslint-disable added |
|---|---|---|---|---|
| Skill invoked (/slop-to-gold) | $0.10 | 13.8 | 0 | 0 |
| Skill loads on its own | $0.10 | 15.8 | 0 | 0 |
| No skill installed (baseline) | $0.04 | 4.4 | 0 | 0 |

**Correction that also asks "make sure it can't come back"**

| Check | Skill invoked (/slop-to-gold) | No skill installed (baseline) |
|---|---|---|
| Skill loaded | 8/8 | n/a |
| Fixed the reported bug | 8/8 | 8/8 |
| Fixed other copies too | 8/8 | 6/8 |
| Added a check that fails on it | 8/8 | 8/8 |
| Check message names the fix | 8/8 | 6/8 |
| Ran lint to verify | 8/8 | 8/8 |
| Lint passes at the end | 8/8 | 6/8 |

| Arm | Avg cost | Avg turns | Runs adding prose rules | eslint-disable added |
|---|---|---|---|---|
| Skill invoked (/slop-to-gold) | $0.10 | 14.5 | 0 | 0 |
| No skill installed (baseline) | $0.08 | 11.6 | 0 | 0 |

**Versus other skills, clean setup** (plain correction)

| Skill | Loaded | Added a failing check | Message names fix | Fixed other copies | Lint passes at end | Wrote prose/notes | Avg cost (API-price estimate) |
|---|---|---|---|---|---|---|---|
| slop-to-gold (loads on its own) | 8/8 | 8/8 | 8/8 | 8/8 | 8/8 | 0/8 | $0.10 |
| slop-to-gold (/slop-to-gold) | 8/8 | 8/8 | 8/8 | 8/8 | 8/8 | 0/8 | $0.10 |
| self-improvement (loads on its own) | 5/8 | 0/8 | 0/8 | 3/8 | 8/8 | 5/8 | $0.09 |
| self-improvement (/self-improvement) | 8/8 | 0/8 | 0/8 | 2/8 | 8/8 | 8/8 | $0.10 |
| Anthropic /revise-claude-md | 8/8 | 0/8 | 0/8 | 2/8 | 8/8 | 2/8 | $0.05 |
| superpowers receiving-code-review | 8/8 | 0/8 | 0/8 | 2/8 | 8/8 | 0/8 | $0.06 |
| no skill (baseline) | n/a | 0/8 | 0/8 | 2/8 | 8/8 | 0/8 | $0.04 |

**Trigger evals, clean setup**

| Prompts | Recall (should load) | False triggers |
|---|---|---|
| Tuned on | 12/12 | 0/12 |
| Held out | 5/6 | 0/6 |

**Audit mode** (2 fixture repos)

| Arm | Changed no source files | Ran scripts/scan.py | Named the planted patterns | Proposed a lint/type/test check | Notes infra gap | Avg cost |
|---|---|---|---|---|---|---|
| Skill loads on its own | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | $0.07 |
| Skill invoked (/slop-to-gold) | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | $0.07 |
| No skill (baseline) | 4/4 | 0/4 | 4/4 | 3/4 | 4/4 | $0.07 |

**Other languages and checks** (plain correction)

| Scenario | Arm | Added a failing check | Names fix | Fixed other copies | Checks pass at end | Prose only | Avg cost |
|---|---|---|---|---|---|---|---|
| Python: utcnow() (ruff) | Skill loads on its own | 2/2 | 2/2 | 2/2 | 2/2 | 0/2 | $0.09 |
| Python: utcnow() (ruff) | Skill invoked (/slop-to-gold) | 2/2 | 2/2 | 2/2 | 2/2 | 0/2 | $0.10 |
| Python: utcnow() (ruff) | No skill (baseline) | 0/2 | 0/2 | 0/2 | 2/2 | 0/2 | $0.06 |
| TypeScript: as any (eslint) | Skill loads on its own | 2/2 | 2/2 | 2/2 | 2/2 | 0/2 | $0.12 |
| TypeScript: as any (eslint) | Skill invoked (/slop-to-gold) | 2/2 | 2/2 | 2/2 | 2/2 | 0/2 | $0.12 |
| TypeScript: as any (eslint) | No skill (baseline) | 2/2 | 0/2 | 2/2 | 2/2 | 0/2 | $0.07 |
| JS: fractional cents (test) | Skill loads on its own | 2/2 | n/a | 2/2 | 2/2 | 0/2 | $0.11 |
| JS: fractional cents (test) | Skill invoked (/slop-to-gold) | 2/2 | n/a | 2/2 | 2/2 | 0/2 | $0.10 |
| JS: fractional cents (test) | No skill (baseline) | 0/2 | n/a | 0/2 | 2/2 | 0/2 | $0.05 |
