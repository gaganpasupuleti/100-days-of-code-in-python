#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "=== Job map (summary) ==="
echo "local-validate     → bash scripts/validate.sh (this machine)"
echo "gh-compile-sources → .github/workflows/validate.yml job compile-sources"
echo "cursor-env-build   → Cursor dashboard / trigger-environment-build (draft)"
echo

echo "=== GitHub: open PRs ==="
if command -v gh >/dev/null 2>&1; then
  gh pr list --repo "$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo gaganpasupuleti/100-days-of-code-in-python)" --state open || true
  echo
  echo "=== GitHub: latest validation workflow runs ==="
  gh run list --workflow=validate.yml --limit 3 2>/dev/null || echo "(no workflow runs or no access)"
else
  echo "gh CLI not available"
fi
echo

echo "=== Local validation (terminal job) ==="
START=$(date +%s)
bash "$ROOT/scripts/validate.sh"
END=$(date +%s)
echo "==> Duration: $((END - START))s"
echo "==> Status: PASS (exit 0)"
