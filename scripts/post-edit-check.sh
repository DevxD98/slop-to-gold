#!/usr/bin/env bash
# PostToolUse hook: after an Edit/Write, run the project's own lint and typecheck.
# Silent (exit 0, no output) unless a check exists AND fails.
# On failure: prints the tail of the output to stderr and exits 2, which feeds it back to Claude.
#
# Only runs when ALL of these hold, so it never nags in projects that haven't opted in:
#   - the edited file is JS/TS
#   - a package.json exists above it
#   - node_modules is installed next to that package.json
#   - package.json has a "lint" and/or "typecheck" script
set -u

input=$(cat)
file=$(printf '%s' "$input" | jq -r '.tool_input.file_path // .tool_response.filePath // empty' 2>/dev/null)
[ -n "$file" ] || exit 0

case "$file" in
  */node_modules/*) exit 0 ;;
  *.ts|*.tsx|*.js|*.jsx|*.mjs|*.cjs) ;;
  *) exit 0 ;;
esac

dir=$(dirname "$file")
while [ "$dir" != "/" ] && [ ! -f "$dir/package.json" ]; do dir=$(dirname "$dir"); done
[ -f "$dir/package.json" ] || exit 0
[ -d "$dir/node_modules" ] || exit 0

has_script() { jq -e --arg s "$1" '.scripts[$s] // empty' "$dir/package.json" >/dev/null 2>&1; }

failed=""
for s in lint typecheck; do
  has_script "$s" || continue
  out=$(cd "$dir" && timeout "${SLOP_HOOK_TIMEOUT:-60}" npm run --silent "$s" 2>&1)
  rc=$?
  if [ $rc -ne 0 ]; then
    failed="${failed}\n[slop-to-gold] 'npm run $s' failed (exit $rc) in $dir after editing $file:\n$(printf '%s' "$out" | tail -n 25)\n"
  fi
done

[ -z "$failed" ] && exit 0
printf '%b' "$failed" >&2
exit 2
