#!/usr/bin/env python3
"""Fetch job posting URLs from public job-board APIs (no Apify)."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "jobs" / "scraped_links.json"

# Per-source cap (0 = no cap). Override: MAX_JOBS_PER_SOURCE=500
MAX_PER_SOURCE = int(os.environ.get("MAX_JOBS_PER_SOURCE", "500"))


def fetch_json(url: str) -> dict | list:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "100-days-job-link-check/1.0"},
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode("utf-8"))


def cap(rows: list[dict]) -> list[dict]:
    if MAX_PER_SOURCE <= 0:
        return rows
    return rows[:MAX_PER_SOURCE]


def row(source: str, title: str, company: str, url: str) -> dict:
    return {"source": source, "title": title, "company": company, "url": url}


def links_from_remotive(payload: dict) -> list[dict]:
    rows: list[dict] = []
    for job in payload.get("jobs", []):
        link = job.get("url") or job.get("job_url")
        if not link:
            continue
        rows.append(
            row(
                "remotive",
                job.get("title", ""),
                job.get("company_name", ""),
                link,
            )
        )
    return cap(rows)


def links_from_arbeitnow(payload: dict | list) -> list[dict]:
    jobs = payload.get("data", []) if isinstance(payload, dict) else payload
    rows: list[dict] = []
    for job in jobs:
        link = job.get("url")
        if not link:
            continue
        rows.append(
            row(
                "arbeitnow",
                job.get("title", ""),
                job.get("company_name", ""),
                link,
            )
        )
    return cap(rows)


def links_from_remoteok(payload: list) -> list[dict]:
    rows: list[dict] = []
    for job in payload:
        if not isinstance(job, dict):
            continue
        link = job.get("url") or job.get("apply_url")
        if not link or not link.startswith("http"):
            continue
        rows.append(
            row(
                "remoteok",
                job.get("position") or job.get("title") or "",
                job.get("company") or "",
                link,
            )
        )
    return cap(rows)


def links_from_jobicy(max_pages: int = 10) -> tuple[list[dict], str | None]:
    rows: list[dict] = []
    cursor: str | None = None
    error: str | None = None
    page_size = 50

    for _ in range(max_pages):
        if MAX_PER_SOURCE > 0 and len(rows) >= MAX_PER_SOURCE:
            break
        params: dict[str, str] = {"count": str(page_size)}
        if cursor:
            params["cursor"] = cursor
        url = "https://jobicy.com/api/v2/remote-jobs?" + urllib.parse.urlencode(params)
        try:
            data = fetch_json(url)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            error = str(exc)
            break
        for job in data.get("jobs", []):
            link = job.get("url")
            if not link:
                continue
            rows.append(
                row(
                    "jobicy",
                    job.get("jobTitle") or job.get("title") or "",
                    job.get("companyName") or "",
                    link,
                )
            )
            if MAX_PER_SOURCE > 0 and len(rows) >= MAX_PER_SOURCE:
                break
        if not data.get("hasMore"):
            break
        cursor = data.get("nextCursor")
        if not cursor:
            break

    return cap(rows), error


def main() -> int:
    all_rows: list[dict] = []
    errors: list[str] = []
    stats: dict[str, int] = {}

    sources: list[tuple[str, callable]] = [
        ("remotive", lambda: links_from_remotive(fetch_json("https://remotive.com/api/remote-jobs"))),
        ("arbeitnow", lambda: links_from_arbeitnow(fetch_json("https://www.arbeitnow.com/api/job-board-api"))),
        ("remoteok", lambda: links_from_remoteok(fetch_json("https://remoteok.com/api"))),
    ]

    for name, fn in sources:
        try:
            batch = fn()
            stats[name] = len(batch)
            all_rows.extend(batch)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            errors.append(f"{name}: {exc}")
            stats[name] = 0

    jobicy_rows, jobicy_err = links_from_jobicy()
    stats["jobicy"] = len(jobicy_rows)
    all_rows.extend(jobicy_rows)
    if jobicy_err:
        errors.append(f"jobicy: {jobicy_err}")

    seen: set[str] = set()
    unique: list[dict] = []
    for row_item in all_rows:
        u = row_item["url"].strip()
        if u in seen:
            continue
        seen.add(u)
        unique.append(row_item)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "scraped_at": datetime.now(UTC).isoformat(),
                "max_per_source": MAX_PER_SOURCE,
                "count": len(unique),
                "by_source_before_dedupe": stats,
                "errors": errors,
                "jobs": unique,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"==> Scraped {len(unique)} unique job links (cap {MAX_PER_SOURCE}/source)")
    print(f"==> By source (raw): {stats}")
    print(f"==> Saved -> {OUT.relative_to(ROOT)}")
    for err in errors:
        print(f"WARN: {err}", file=sys.stderr)
    return 0 if unique else 1


if __name__ == "__main__":
    raise SystemExit(main())
