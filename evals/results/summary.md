**Trigger evals** (2 runs per prompt)

| Description | Recall (should load) | False triggers |
|---|---|---|
| Old description | 10/12 | 0/12 |
| New description | 12/12 | 0/12 |

**Plain correction: "you did X again, fix it"**

| Check | Skill invoked (/slop-to-gold) | Skill loads on its own | Skill blocked (baseline) | Loads on its own (old description) |
|---|---|---|---|---|
| Skill loaded | 8/8 | 8/8 | 0/8 | 0/8 |
| Fixed the reported bug | 8/8 | 8/8 | 8/8 | 8/8 |
| Fixed other copies too | 8/8 | 6/8 | 2/8 | 2/8 |
| Added a check that fails on it | 8/8 | 8/8 | 0/8 | 0/8 |
| Check message names the fix | 7/8 | 7/8 | 0/8 | 0/8 |
| Ran lint to verify | 8/8 | 8/8 | 3/8 | 3/8 |
| Lint passes at the end | 8/8 | 6/8 | 8/8 | 8/8 |

| Arm | Avg cost | Avg turns | Runs adding prose rules | eslint-disable added |
|---|---|---|---|---|
| Skill invoked (/slop-to-gold) | $0.16 | 12.8 | 0 | 0 |
| Skill loads on its own | $0.15 | 14.5 | 0 | 0 |
| Skill blocked (baseline) | $0.11 | 4.9 | 0 | 0 |
| Loads on its own (old description) | $0.11 | 4.6 | 0 | 0 |

**Correction that also asks "make sure it can't come back"**

| Check | Skill invoked (/slop-to-gold) | Skill blocked (baseline) |
|---|---|---|
| Skill loaded | 8/8 | 0/8 |
| Fixed the reported bug | 8/8 | 8/8 |
| Fixed other copies too | 8/8 | 7/8 |
| Added a check that fails on it | 8/8 | 8/8 |
| Check message names the fix | 8/8 | 6/8 |
| Ran lint to verify | 8/8 | 8/8 |
| Lint passes at the end | 8/8 | 7/8 |

| Arm | Avg cost | Avg turns | Runs adding prose rules | eslint-disable added |
|---|---|---|---|---|
| Skill invoked (/slop-to-gold) | $0.16 | 13.0 | 0 | 0 |
| Skill blocked (baseline) | $0.15 | 12.1 | 0 | 0 |

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
