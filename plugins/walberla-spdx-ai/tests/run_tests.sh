#!/usr/bin/env bash

# SPDX-FileCopyrightText: 2026 Michael Zikeli <63597338+Pitt0s@users.noreply.github.com>
# SPDX-FileContributor: Claude Code (claude-opus-5-5)
#
# SPDX-License-Identifier: CC0-1.0

# SPDX-FileCreatedBy: Michael Zikeli
# SPDX-FileCreatedUsing: Claude Code (claude-opus-5-5)

# Smoke tests for check_spdx.py. Run from the repository root.
# Requires the reuse tool (pipx install reuse).
set -u
S="skills/spdx-ai-annotation/scripts/check_spdx.py"
P="tests/fixtures/project/apps"
fail=0

expect() {  # expect <exit code> <description> <command...>
  local want="$1" desc="$2"; shift 2
  "$@" >/dev/null 2>&1; local got=$?
  if [ "$got" -eq "$want" ]; then echo "PASS  $desc"; else echo "FAIL  $desc (exit $got, want $want)"; fail=1; fi
}
hook() { echo "{\"tool_name\":\"$1\",\"tool_input\":{\"file_path\":\"$2\"}}" | python3 "$S" --hook; }

command -v reuse >/dev/null || { echo "reuse not installed"; exit 1; }

expect 0 "human file with AI snippet"        python3 "$S" "$P/human_with_snippet.cpp"
expect 0 "AI C++ header"                     python3 "$S" "$P/ai_file.h"
expect 0 "AI Python file with shebang"       python3 "$S" "$P/ai_script.py"
expect 0 "binary file with .license sidecar" python3 "$S" "$P/mesh.bin"
expect 1 "deprecated CC-0 identifier"        python3 "$S" "$P/bad_cc-0.h"
expect 1 "unclosed snippet"                  python3 "$S" "$P/bad_unclosed.cpp"
expect 1 "unfilled placeholder"              python3 "$S" "$P/bad_placeholder.h"
expect 1 "policy block lost after annotate"  python3 "$S" "$P/bad_lost_block.cpp"
expect 1 "AI header without copyright"       python3 "$S" "$P/bad_no_ai_copyright.cpp"
expect 1 "legacy file without header"        python3 "$S" "$P/legacy.cpp"
expect 0 "legacy file with --no-header-check" python3 "$S" --no-header-check "$P/legacy.cpp"
expect 0 "examples inside REUSE ignore region" python3 "$S" "$P/doc_example.md"
expect 1 "AI code in core path"              python3 "$S" "tests/fixtures/project/src/core/Thing.h"
expect 0 "hook: Edit (refactoring) of legacy file" hook Edit  "$P/legacy.cpp"
expect 2 "hook: Write of file without header"      hook Write "$P/legacy.cpp"
expect 2 "hook: Edit leaves snippet open"          hook Edit  "$P/bad_unclosed.cpp"

out=$(python3 "$S" --project-license tests/fixtures/project)
echo "$out" | grep -q '"license": "GPL-3.0-or-later"' \
  && echo "PASS  project license from LICENSES/" || { echo "FAIL  project license from LICENSES/"; fail=1; }

tmp=$(mktemp -d); cp tests/fixtures/project/COPYING.txt "$tmp/"; echo '{}' > "$tmp/.spdx-ai.json"
python3 "$S" --project-license "$tmp" | grep -q '"ambiguous": true' \
  && echo "PASS  GPL text without LICENSES/ is ambiguous" || { echo "FAIL  GPL ambiguity"; fail=1; }
rm -rf "$tmp"

exit $fail
