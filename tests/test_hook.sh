#!/usr/bin/env bash
# Contract tests for scripts/post-edit-check.sh.
# Each case builds a tiny project, pipes a PostToolUse payload into the hook,
# and checks the exit code and stderr. Prints one TSV row per case to stdout
# (name, expected, actual, ms, pass) so results can be charted.
#
# Run: bash tests/test_hook.sh
set -u
HOOK="$(cd "$(dirname "$0")/.." && pwd)/scripts/post-edit-check.sh"
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
fails=0

# mkproj <dir> <lint-cmd|-> <typecheck-cmd|-> [no-modules]
mkproj() {
  local d="$1" lint="$2" tc="$3"
  mkdir -p "$d/src"
  [ "${4:-}" = "no-modules" ] || mkdir -p "$d/node_modules"
  local scripts="{}"
  [ "$lint" != "-" ] && scripts=$(jq -n --argjson s "$scripts" --arg v "$lint" '$s + {lint: $v}')
  [ "$tc" != "-" ] && scripts=$(jq -n --argjson s "$scripts" --arg v "$tc" '$s + {typecheck: $v}')
  jq -n --argjson s "$scripts" '{name: "t", private: true, scripts: $s}' > "$d/package.json"
}

PASS='node -e "process.exit(0)"'
FAIL='node -e "console.log(\"LINT-ERROR setTimeout banned\"); process.exit(1)"'
TCFAIL='node -e "console.log(\"TS2322 type error\"); process.exit(1)"'
SLOW='node -e "setTimeout(()=>{}, 5000)"'

# case <name> <expected-exit> <payload-json> [stderr-must-contain]
case_() {
  local name="$1" want="$2" payload="$3" needle="${4:-}"
  local start end err rc ok=PASS
  start=$(python3 -c 'import time; print(int(time.time()*1000))')
  err=$(printf '%s' "$payload" | SLOP_HOOK_TIMEOUT=2 bash "$HOOK" 2>&1 >/dev/null)
  rc=$?
  end=$(python3 -c 'import time; print(int(time.time()*1000))')
  [ "$rc" = "$want" ] || ok=FAIL
  if [ -n "$needle" ] && ! printf '%s' "$err" | grep -q -- "$needle"; then ok=FAIL; fi
  if [ "$want" = 0 ] && [ -n "$err" ]; then ok=FAIL; fi   # passes must be silent
  [ "$ok" = PASS ] || fails=$((fails + 1))
  printf '%s\t%s\t%s\t%s\t%s\n' "$name" "$want" "$rc" "$((end - start))" "$ok"
}

p() { jq -cn --arg f "$1" '{tool_name: "Edit", tool_input: {file_path: $f}}'; }

mkproj "$T/ok" "$PASS" "$PASS";            touch "$T/ok/src/a.ts"
mkproj "$T/bad" "$FAIL" "-";               touch "$T/bad/src/a.ts"
mkproj "$T/tc" "$PASS" "$TCFAIL";          touch "$T/tc/src/a.tsx"
mkproj "$T/both" "$FAIL" "$TCFAIL";        touch "$T/both/src/a.js"
mkproj "$T/nomods" "$FAIL" "-" no-modules; touch "$T/nomods/src/a.ts"
mkproj "$T/noscripts" "-" "-";             touch "$T/noscripts/src/a.ts"
mkproj "$T/sp ace" "$FAIL" "-";            touch "$T/sp ace/src/a.ts"
mkproj "$T/slow" "$SLOW" "-";              touch "$T/slow/src/a.ts"
mkproj "$T/mono" "$PASS" "-"
mkproj "$T/mono/packages/web" "$FAIL" "-"; touch "$T/mono/packages/web/src/a.ts"
mkdir -p "$T/ok/node_modules/dep";         touch "$T/ok/node_modules/dep/i.js"

{
printf 'case\texpected\tactual\tms\tresult\n'
case_ "lint passes -> silent"            0 "$(p "$T/ok/src/a.ts")"
case_ "lint fails -> feedback"           2 "$(p "$T/bad/src/a.ts")" "LINT-ERROR setTimeout banned"
case_ "typecheck fails -> feedback"      2 "$(p "$T/tc/src/a.tsx")" "npm run typecheck"
case_ "both fail -> both reported"       2 "$(p "$T/both/src/a.js")" "npm run typecheck"
case_ "no node_modules -> skip"          0 "$(p "$T/nomods/src/a.ts")"
case_ "no lint/typecheck scripts -> skip" 0 "$(p "$T/noscripts/src/a.ts")"
case_ "non-JS file -> skip"              0 "$(p "$T/bad/README.md")"
case_ "file in node_modules -> skip"     0 "$(p "$T/ok/node_modules/dep/i.js")"
case_ "empty payload -> skip"            0 '{}'
case_ "malformed JSON -> skip"           0 'not json'
case_ "path with spaces"                 2 "$(p "$T/sp ace/src/a.ts")" "LINT-ERROR"
case_ "monorepo uses nearest package"    2 "$(p "$T/mono/packages/web/src/a.ts")" "packages/web"
case_ "tool_response.filePath fallback"  2 "$(jq -cn --arg f "$T/bad/src/a.ts" '{tool_name: "Write", tool_input: {}, tool_response: {filePath: $f}}')" "LINT-ERROR"
case_ "slow lint -> timeout reported"    2 "$(p "$T/slow/src/a.ts")" "exit 124"
} | tee "${HOOK_RESULTS:-/dev/null}"

echo "failures: $fails" >&2
exit $(( fails > 0 ))
