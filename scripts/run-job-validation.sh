#!/usr/bin/env bash
# Start a full local job run: status check + validation. See docs/job-map.md for mapping.
set -euo pipefail
exec bash "$(dirname "$0")/job-status.sh"
