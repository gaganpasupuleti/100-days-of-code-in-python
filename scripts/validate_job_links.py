#!/usr/bin/env python3
"""Check whether scraped job URLs respond (active vs dead/blocked)."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INP = ROOT / "jobs" / "scraped_links.json"
OUT = ROOT / "jobs" / "link_validation.json"


def probe(url: str) -> dict:
    req = urllib.request.Request(
        url,
        method="HEAD",
        headers={"User-Agent": "100-days-job-link-check/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return {
                "url": url,
                "status": resp.status,
                "final_url": resp.geturl(),
                "active": 200 <= resp.status < 400,
                "method": "HEAD",
            }
    except urllib.error.HTTPError as exc:
        if exc.code in (403, 405, 429):
            return probe_get(url)
        return {
            "url": url,
            "status": exc.code,
            "final_url": url,
            "active": False,
            "method": "HEAD",
            "error": str(exc.reason),
        }
    except urllib.error.URLError as exc:
        return {
            "url": url,
            "status": None,
            "final_url": url,
            "active": False,
            "method": "HEAD",
            "error": str(exc.reason),
        }


def probe_get(url: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "100-days-job-link-check/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return {
                "url": url,
                "status": resp.status,
                "final_url": resp.geturl(),
                "active": 200 <= resp.status < 400,
                "method": "GET",
            }
    except urllib.error.HTTPError as exc:
        return {
            "url": url,
            "status": exc.code,
            "final_url": url,
            "active": 200 <= exc.code < 400,
            "method": "GET",
            "error": str(exc.reason),
        }
    except urllib.error.URLError as exc:
        return {
            "url": url,
            "status": None,
            "final_url": url,
            "active": False,
            "method": "GET",
            "error": str(exc.reason),
        }


def main() -> int:
    if not INP.is_file():
        print(f"Missing {INP.relative_to(ROOT)} — run scrape_job_links.py first", file=sys.stderr)
        return 1

    payload = json.loads(INP.read_text(encoding="utf-8"))
    jobs = payload.get("jobs", [])
    results: list[dict] = []
    active = 0
    inactive = 0

    for job in jobs:
        url = job["url"]
        row = probe(url)
        row["title"] = job.get("title", "")
        row["source"] = job.get("source", "")
        results.append(row)
        if row["active"]:
            active += 1
        else:
            inactive += 1

    OUT.write_text(
        json.dumps(
            {
                "validated_at": datetime.now(UTC).isoformat(),
                "total": len(results),
                "active": active,
                "inactive": inactive,
                "results": results,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"==> Validated {len(results)} links: {active} active, {inactive} inactive")
    print(f"==> Report -> {OUT.relative_to(ROOT)}")
    step = max(1, len(results) // 10)
    for i, row in enumerate(results):
        if i % step == 0 or i == len(results) - 1:
            flag = "OK" if row["active"] else "DEAD"
            print(f"  [{flag}] {row['status']} {row['url'][:72]}...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
