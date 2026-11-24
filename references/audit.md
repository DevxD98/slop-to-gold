# Audit

Find the weeds agents will copy.

1. Run `python3 scripts/scan.py <repo-path>` for a first pass. It counts the usual suspects and prints the top files.
2. Read the top few hits yourself; the script gives candidates, not verdicts.
3. Group findings into patterns, and rank by how often agents will meet them (frequency x visibility).
4. For each top pattern, propose one check from `correction-to-check.md` order, with the expected number of violations.
5. Present a short ranked list. Do not change code until the user picks which patterns to fix.

Check also: do lint, typecheck and tests exist and run? If not, that gap comes before everything else.
