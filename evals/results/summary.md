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
