#!/usr/bin/env python3
"""
NCEA Batch Crawler — crawl all metrics for target schools.

Skips (school, metric) pairs that already succeeded in scrape_log.
Usage:
    python -m crawlers.batch_ncea
    python -m crawlers.batch_ncea --school 65       # single school
    python -m crawlers.batch_ncea --dry-run          # show plan only
"""

import argparse
import random
import sqlite3
import time
from pathlib import Path

from .ncea_crawler import METRICS, scrape_school

DB_PATH = Path(__file__).resolve().parent.parent / "schools.db"

TARGET_SCHOOLS = [
    (6930, "Botany Downs Secondary College"),
    (65,   "Glendowie College"),
    (27,   "Long Bay College"),
    (75,   "Lynfield College"),
    (69,   "Mt Albert Grammar School"),
    (32,   "Northcote College"),
    (28,   "Rangitoto College"),
    (49,   "Selwyn College"),
    (36,   "Takapuna Grammar School"),
    (48,   "Western Springs College"),
]

ALL_METRICS = list(METRICS.keys())


def get_completed_metrics(school_number):
    """Return set of metrics already successfully scraped for a school."""
    conn = sqlite3.connect(str(DB_PATH))
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT DISTINCT metric FROM scrape_log WHERE school_number = ? AND success = 1",
            (school_number,),
        )
        return {row[0] for row in cur.fetchall()}
    finally:
        conn.close()


def run_batch(single_school=None, dry_run=False):
    schools = TARGET_SCHOOLS
    if single_school:
        schools = [(n, name) for n, name in TARGET_SCHOOLS if n == single_school]
        if not schools:
            print(f"  School {single_school} not in target list.")
            return

    print(f"\n{'='*60}")
    print(f"  NCEA Batch Crawler")
    print(f"  Schools: {len(schools)}")
    print(f"  Metrics per school: {', '.join(ALL_METRICS)}")
    print(f"{'='*60}\n")

    plan = []
    for num, name in schools:
        done = get_completed_metrics(num)
        pending = [m for m in ALL_METRICS if m not in done]
        plan.append((num, name, done, pending))
        status = "✅ all done" if not pending else f"pending: {', '.join(pending)}"
        skipped = f" (skip: {', '.join(done)})" if done else ""
        print(f"  #{num:<5} {name:<40} {status}{skipped}")

    total_pending = sum(len(p[3]) for p in plan)
    print(f"\n  Total pages to crawl: {total_pending}")

    if dry_run:
        print("  [DRY RUN] No crawling performed.")
        return

    if total_pending == 0:
        print("  Nothing to crawl — all done!")
        return

    print(f"\n  Starting in 5 seconds...\n")
    time.sleep(5)

    results = []
    for i, (num, name, done, pending) in enumerate(plan):
        if not pending:
            continue

        print(f"\n  [{i+1}/{len(plan)}] {name} (#{num}) — {len(pending)} metrics")

        try:
            result = scrape_school(num, only=pending, delay_range=(10, 15))
            perf_rows = len(result.get("performance", []))
            comp_rows = len(result.get("comparison", []))
            results.append((num, name, "OK", perf_rows, comp_rows))
        except Exception as e:
            print(f"  ❌ Error crawling {name}: {e}")
            results.append((num, name, f"ERROR: {e}", 0, 0))

        # Extra pause between schools
        if i < len(plan) - 1:
            pause = random.uniform(30, 60)
            print(f"\n  Pausing {pause:.0f}s before next school...")
            time.sleep(pause)

    # Final summary
    print(f"\n{'='*60}")
    print(f"  Batch Crawl Complete")
    print(f"{'='*60}")
    for num, name, status, perf, comp in results:
        print(f"  #{num:<5} {name:<40} {status} (perf:{perf}, comp:{comp})")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="NCEA Batch Crawler")
    parser.add_argument("--school", type=int, help="Crawl single school only")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without crawling")
    args = parser.parse_args()

    run_batch(single_school=args.school, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
