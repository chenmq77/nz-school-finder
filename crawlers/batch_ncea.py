#!/usr/bin/env python3
"""
NCEA Batch Crawler — crawl all metrics for target schools (569 secondary/composite).

Skips (school, metric) pairs that already have status=success or status=no_data.
Retries failed/timeout/parse_error entries.

Usage:
    python -m crawlers.batch_ncea --dry-run
    python -m crawlers.batch_ncea --batch-size 50 --offset 0
    python -m crawlers.batch_ncea --batch-size 50 --offset 50
    python -m crawlers.batch_ncea --school 65
    python -m crawlers.batch_ncea --strict --dry-run
"""

import argparse
import os
import random
import shutil
import sqlite3
import time
from datetime import datetime
from pathlib import Path

from .ncea_crawler import METRICS, scrape_school

DB_PATH = Path(os.environ.get(
    "SCHOOLS_DB",
    str(Path(__file__).resolve().parent.parent / "schools.db")
))

ALL_METRICS = list(METRICS.keys())

EXPECTED_SCHOOL_COUNT = 569
SCHOOL_COUNT_TOLERANCE = 0.10  # 10%

# Circuit breaker settings
MAX_CONSECUTIVE_FAILURES = 5
CIRCUIT_BREAKER_PAUSE_SECONDS = 600  # 10 minutes


def ensure_status_column(db_path=None):
    """Add status column to scrape_log if missing, and backfill from legacy success field."""
    conn = sqlite3.connect(str(db_path or DB_PATH))
    try:
        cur = conn.cursor()
        # Check if status column exists
        cur.execute("PRAGMA table_info(scrape_log)")
        columns = {row[1] for row in cur.fetchall()}
        if "status" not in columns:
            print("  [MIGRATION] Adding status column to scrape_log...")
            cur.execute("ALTER TABLE scrape_log ADD COLUMN status TEXT DEFAULT 'success'")
            cur.execute(
                "UPDATE scrape_log SET status = CASE "
                "WHEN success = 1 THEN 'success' ELSE 'failed' END"
            )
            conn.commit()
            print("  [MIGRATION] Done — backfilled existing rows.")
    finally:
        conn.close()


def get_target_schools(db_path=None):
    """Query all secondary/composite schools from DB, ordered by school_number."""
    conn = sqlite3.connect(str(db_path or DB_PATH))
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT school_number, school_name FROM schools "
            "WHERE school_type LIKE '%Secondary%' "
            "   OR school_type LIKE '%Composite%' "
            "ORDER BY school_number"
        )
        return cur.fetchall()
    finally:
        conn.close()


def get_completed_metrics(school_number, db_path=None):
    """Return set of metrics with status=success or status=no_data (skip on resume)."""
    conn = sqlite3.connect(str(db_path or DB_PATH))
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT DISTINCT metric FROM scrape_log "
            "WHERE school_number = ? AND status IN ('success', 'no_data')",
            (school_number,),
        )
        return {row[0] for row in cur.fetchall()}
    finally:
        conn.close()


def auto_backup_db(db_path=None):
    """Create a timestamped backup of the database."""
    src = db_path or DB_PATH
    if not src.exists():
        print(f"  [WARN] DB not found at {src}, skipping backup")
        return None
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = src.parent / f"schools_backup_{timestamp}.db"
    shutil.copy2(str(src), str(backup_path))
    size_mb = backup_path.stat().st_size / (1024 * 1024)
    print(f"  ✅ Backup created: {backup_path.name} ({size_mb:.1f} MB)")
    return backup_path


def run_batch(batch_size=None, offset=0, single_school=None, dry_run=False, strict=False):
    """Run batch crawl with optional slicing, resume, and circuit breaker."""

    # Ensure schema is up to date
    ensure_status_column()

    # Get target schools
    all_schools = get_target_schools()
    school_count = len(all_schools)
    print(f"\n{'='*60}")
    print(f"  NCEA Batch Crawler")
    print(f"  Found {school_count} target schools (expected ~{EXPECTED_SCHOOL_COUNT})")
    print(f"{'='*60}\n")

    # Validate school count
    deviation = abs(school_count - EXPECTED_SCHOOL_COUNT) / EXPECTED_SCHOOL_COUNT
    if school_count < 500 or school_count > 650:
        print(f"  ⚠️  School count {school_count} outside expected range 500-650")
    if strict and deviation > SCHOOL_COUNT_TOLERANCE:
        print(f"  ⛔ Deviation {deviation:.0%} > {SCHOOL_COUNT_TOLERANCE:.0%} "
              f"— aborting (--strict mode)")
        return

    # Single school mode
    if single_school:
        single_str = str(single_school)
        all_schools = [(n, name) for n, name in all_schools if str(n) == single_str]
        if not all_schools:
            print(f"  School {single_school} not in target list.")
            return

    # Apply offset/batch-size slice (deterministic, on full ordered list)
    if batch_size is not None:
        all_schools = all_schools[offset:offset + batch_size]
        print(f"  Batch: offset={offset}, size={batch_size} → {len(all_schools)} schools")

    # Build plan: check what's already done
    plan = []
    total_pending = 0
    completed_schools = 0
    for num, name in all_schools:
        done = get_completed_metrics(num)
        pending = [m for m in ALL_METRICS if m not in done]
        plan.append((num, name, done, pending))
        total_pending += len(pending)
        if not pending:
            completed_schools += 1
        status = "✅ all done" if not pending else f"pending: {', '.join(pending)}"
        skipped = f" (skip: {', '.join(done)})" if done else ""
        print(f"  #{num:<5} {name:<40} {status}{skipped}")

    # Aggregate stats
    pending_schools = len(all_schools) - completed_schools
    est_seconds = total_pending * 18  # ~18s per page
    est_minutes = est_seconds / 60
    print(f"\n  Summary:")
    print(f"    Target schools:    {len(all_schools)}")
    print(f"    Completed schools: {completed_schools}")
    print(f"    Pending schools:   {pending_schools}")
    print(f"    Pending pages:     {total_pending}")
    print(f"    Estimated time:    {est_minutes:.0f} minutes ({est_minutes/60:.1f} hours)")

    if dry_run:
        print("\n  [DRY RUN] No crawling performed.")
        return

    if total_pending == 0:
        print("  Nothing to crawl — all done!")
        return

    # Auto backup
    print(f"\n  Creating database backup...")
    auto_backup_db()

    print(f"\n  Starting in 5 seconds...\n")
    time.sleep(5)

    # Crawl with metric-level circuit breaker
    consecutive_failures = 0
    breaker_tripped_once = False
    results = []
    start_time = time.time()
    schools_with_pending = [(num, name, pending) for num, name, _, pending in plan if pending]

    for i, (num, name, pending) in enumerate(schools_with_pending):
        elapsed = time.time() - start_time
        remaining_schools = len(schools_with_pending) - i
        avg_per_school = elapsed / max(i, 1)
        eta_minutes = (remaining_schools * avg_per_school) / 60

        print(f"\n  [{i+1}/{len(schools_with_pending)}] {name} (#{num}) "
              f"— {len(pending)} metrics | ETA: {eta_minutes:.0f}min")

        try:
            result = scrape_school(num, only=pending, delay_range=(10, 15))
            perf_rows = len(result.get("performance", []))
            comp_rows = len(result.get("comparison", []))
            results.append((num, name, "OK", perf_rows, comp_rows))

            # Circuit breaker: track metric-level statuses
            for s in result.get("statuses", []):
                if s in ("failed", "timeout"):
                    consecutive_failures += 1
                else:
                    consecutive_failures = 0  # Reset on success or no_data

        except Exception as e:
            print(f"  ❌ Error crawling {name}: {e}")
            results.append((num, name, f"ERROR: {e}", 0, 0))
            consecutive_failures += len(pending)  # Count all pending as failures

        # Circuit breaker trigger
        if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            print(f"\n  🔴 Circuit breaker: {consecutive_failures} consecutive metric failures!")
            print(f"  Pausing {CIRCUIT_BREAKER_PAUSE_SECONDS // 60} minutes before retry...")
            time.sleep(CIRCUIT_BREAKER_PAUSE_SECONDS)
            consecutive_failures = 0
            if breaker_tripped_once:
                print(f"  ⛔ Circuit breaker tripped twice. Aborting batch crawl.")
                print(f"  Resume later with same command.")
                break
            breaker_tripped_once = True
            print(f"  🟡 Resumed after pause. Next failure burst will abort.")

        # Pause between schools
        if i < len(schools_with_pending) - 1:
            pause = random.uniform(30, 60)
            print(f"\n  Pausing {pause:.0f}s before next school...")
            time.sleep(pause)

    # Final summary
    elapsed_total = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"  Batch Crawl Complete")
    print(f"  Duration: {elapsed_total/60:.0f} minutes")
    print(f"{'='*60}")
    for num, name, status, perf, comp in results:
        print(f"  #{num:<5} {name:<40} {status} (perf:{perf}, comp:{comp})")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="NCEA Batch Crawler")
    parser.add_argument("--school", type=int, help="Crawl single school only")
    parser.add_argument("--batch-size", type=int, help="Number of schools per batch")
    parser.add_argument("--offset", type=int, default=0, help="Start position in ordered school list")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without crawling")
    parser.add_argument("--strict", action="store_true", help="Abort if school count deviates >10%")
    args = parser.parse_args()

    run_batch(
        batch_size=args.batch_size,
        offset=args.offset,
        single_school=args.school,
        dry_run=args.dry_run,
        strict=args.strict,
    )


if __name__ == "__main__":
    main()
