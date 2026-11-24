# Correction to check

Run this when the user corrects you or the same mistake appears twice.

1. **State the mistake as a pattern**, not an instance. Example: "calls setTimeout to patch timing", not "line 42 was wrong".
2. **Pick the strongest check that fits**, in this order:
   1. Change the API or architecture so the mistake can't be written.
   2. Type or compiler constraint.
   3. Lint rule (ESLint `no-restricted-syntax`/`no-restricted-imports`, ast-grep, ruff, semgrep).
   4. Dependency boundary (dependency-cruiser, import-linter) plus a directory convention.
   5. Test or script in CI.
   6. Prose line, only if 1-5 are impossible. Say why.
3. **Write the check with a teaching error**: name the banned thing, give the root-cause fix, and point to the allowed alternative.
   - Built-in rules such as `no-console` or `no-alert` print a fixed message ("Unexpected console statement.") that teaches nothing. Use `no-restricted-syntax`, `no-restricted-properties` or `no-restricted-imports` instead, so you can write the message.
4. **Prove it**: run it against the bad pattern and confirm it fails; run it on the repo and list existing violations.
   - If the linter isn't installed, run it from a throwaway directory (`npx --yes eslint` in a temp dir with the rule copied in, or ESLint's stdin mode with `--stdin-filename`). If that is not possible, mark the rule **unverified** in your report and give the exact command the user should run.
   - Before enabling a broad ban, list the existing uses. Add the legitimate ones to an explicit allowlist (an `overrides` entry for those files), not to a comment.
5. **Leave lint passing.** For every other violation the new check finds:
   - Same mistake, same mechanical fix (as in the file the user named): fix it now and list it in your report.
   - Fixing it would change behavior, or there are more than 5: add those files to an explicit allowlist (an `overrides` entry turning the rule off for exactly those files), list them, and offer the cleanup as a separate step.
   Never finish with the new check failing on code you left alone.
6. **Do not add comments** explaining why a workaround is fine. If a workaround is needed, the check should have an explicit allowlist entry instead.

Candidates worth banning outright: APIs that need nuance to use well (React `useEffect` in product code), imperative timers as quick fixes, cross-layer imports, and comments that justify skipping the right fix.
