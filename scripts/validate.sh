#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> Python: $(python3 --version)"
PY_COUNT="$(find sources -name '*.py' | wc -l | tr -d ' ')"
echo "==> Compiling ${PY_COUNT} Python files under sources/"
python3 -m compileall -q sources
echo "==> Validation passed"
