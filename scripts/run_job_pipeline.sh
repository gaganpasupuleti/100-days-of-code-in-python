#!/usr/bin/env bash
# Scrape new job links, then check if URLs are active. Not Python compileall CI.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
echo "=== Job pipeline: scrape -> validate links ==="
python3 "$ROOT/scripts/scrape_job_links.py"
python3 "$ROOT/scripts/validate_job_links.py"
