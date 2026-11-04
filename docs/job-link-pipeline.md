# Job link pipeline (recruitment URLs)

This is **not** Python `compileall` CI. It scrapes **job posting links** and checks if URLs still respond.

## Run in terminal (PC, Termux, or Cloud Agent)

```bash
bash scripts/run_job_pipeline.sh
```

Or step by step:

```bash
python3 scripts/scrape_job_links.py    # writes jobs/scraped_links.json
python3 scripts/validate_job_links.py  # writes jobs/link_validation.json
```

## What it does

| Step | Script | Output |
|------|--------|--------|
| 1. New job run (scrape) | `scrape_job_links.py` | Remotive, Arbeitnow (~300), RemoteOK (~99), Jobicy (paginated) → `jobs/scraped_links.json` |
| 2. Validate links | `validate_job_links.py` | HTTP HEAD/GET each URL; marks **active** (2xx/3xx) vs **inactive** |

## Repo note

`main` is the 100 Days of Python course only. Job scraping lives on branch `cursor/job-run-validation-8111` until merged.

Apify is **not** required for this pipeline.
