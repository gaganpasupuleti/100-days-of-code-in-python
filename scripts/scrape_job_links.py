#!/usr/bin/env python3
"""Fetch job posting URLs from public job-board APIs (no Apify)."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "jobs" / "scraped_links.json"

SOURCES = (
    {
        "name": "remotive",
        "url": "https://remotive.com/api/remote-jobs",
    },
    {
        "name": "arbeitnow",
        "url": "https://www.arbeitnow.com/api/job-board-api",
    },
)


def fetch_json(url: str) -> dict | list:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "100-days-job-link-check/1.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def links_from_remotive(payload: dict) -> list[dict]:
    rows: list[dict] = []
    for job in payload.get("jobs", [])[:25]:
        link = job.get("url") or job.get("job_url")
        if not link:
            continue
        rows.append(
            {
                "source": "remotive",
                "title": job.get("title", ""),
                "company": job.get("company_name", ""),
                "url": link,
            }
        )
    return rows


def links_from_arbeitnow(payload: dict | list) -> list[dict]:
    jobs = payload.get("data", []) if isinstance(payload, dict) else payload
    rows: list[dict] = []
    for job in jobs[:25]:
        link = job.get("url")
        if not link:
            continue
        rows.append(
            {
                "source": "arbeitnow",
                "title": job.get("title", ""),
                "company": job.get("company_name", ""),
                "url": link,
            }
        )
    return rows


def main() -> int:
    all_rows: list[dict] = []
    errors: list[str] = []

    for src in SOURCES:
        try:
            data = fetch_json(src["url"])
            if src["name"] == "remotive":
                all_rows.extend(links_from_remotive(data))
            else:
                all_rows.extend(links_from_arbeitnow(data))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            errors.append(f"{src['name']}: {exc}")

    seen: set[str] = set()
    unique: list[dict] = []
    for row in all_rows:
        u = row["url"].strip()
        if u in seen:
            continue
        seen.add(u)
        unique.append(row)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "scraped_at": datetime.now(UTC).isoformat(),
                "count": len(unique),
                "errors": errors,
                "jobs": unique,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"==> Scraped {len(unique)} unique job links -> {OUT.relative_to(ROOT)}")
    for err in errors:
        print(f"WARN: {err}", file=sys.stderr)
    return 0 if unique else 1


if __name__ == "__main__":
    raise SystemExit(main())
