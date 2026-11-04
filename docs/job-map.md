# Job map — validation & CI

Where each “job” runs, how it is triggered, and how steps connect.

## Layer overview

| Job ID | Name | Where it runs | Trigger | Open / active when |
|--------|------|---------------|---------|-------------------|
| `local-validate` | Terminal validation | Cloud Agent VM (or your PC) | `bash scripts/validate.sh` | Any time you run the command |
| `gh-compile-sources` | GitHub Actions `compileall (sources/)` | GitHub-hosted `ubuntu-latest` | Push to `main`, or PR sync | PR **open** or push to `main` |
| `cursor-env-build` | Cursor environment draft build | Cursor build pod | Manual draft / recurring system | Build status `IN_PROGRESS` |

## GitHub workflow steps (`.github/workflows/validate.yml`)

| Step # | Step name | Action |
|--------|-----------|--------|
| 1 | *(checkout)* | `actions/checkout@v4` — clone PR branch |
| 2 | *(setup Python)* | `actions/setup-python@v5` — Python **3.12** |
| 3 | Run validation script | `bash scripts/validate.sh` → `compileall` on `sources/` |

**Workflow job:** `compile-sources` (display name: `compileall (sources/)`).

## Local script steps (`scripts/validate.sh`)

| Step | What it does |
|------|----------------|
| 1 | Print Python version |
| 2 | Count `*.py` under `sources/` |
| 3 | `python3 -m compileall -q sources` |
| 4 | Print `Validation passed` (exit 0) |

## Cursor environment build (install phase)

When `install` is set to `bash scripts/validate.sh`, the build runs the same steps as local validation after platform setup (clone, VM tools, snapshot).

## Typical duration (this repo)

| Job | Usual ETA |
|-----|-----------|
| `local-validate` | **&lt; 5 seconds** |
| `gh-compile-sources` | **~30–90 s** queue + **~5–15 s** run |
| `cursor-env-build` | **~1–2 minutes** (install + snapshot) |

## Open items checklist

Run `bash scripts/job-status.sh` for a live report (PR state, latest Actions run, local validation).
