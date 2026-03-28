#!/usr/bin/env python3
"""
Merge NCEA data from a worktree (source) DB into the main (target) DB.

Uses ATTACH + INSERT OR IGNORE to safely merge without overwriting existing data.
Only merges NCEA-related tables that are exclusively written by the crawler.

Usage:
    python scripts/merge_db.py --source ../learning-ncea-crawl/schools.db
    python scripts/merge_db.py --source ../learning-ncea-crawl/schools.db --verify
    python scripts/merge_db.py --source ../learning-ncea-crawl/schools.db --target ./schools.db
"""

import argparse
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_TARGET = Path(os.environ.get(
    "SCHOOLS_DB",
    str(Path(__file__).resolve().parent.parent / "schools.db")
))

# Only merge these tables — they are exclusively written by the NCEA crawler
MERGE_TABLES = [
    {
        "name": "school_performance",
        "columns": "school_number, year, metric, group_name, below_count, above_count, percentage, is_suppressed, raw_value",
    },
    {
        "name": "school_performance_comparison",
        "columns": "school_number, comparison_group, year, metric, below_count, above_count, percentage",
    },
    {
        "name": "school_vocational_pathways",
        "columns": "school_number, year, group_name, pathway, count, is_suppressed",
    },
    {
        "name": "scrape_log",
        "columns": "school_number, metric, source_url, scraped_at, http_status, content_hash, success, status",
    },
]


def count_rows(conn, table):
    cur = conn.cursor()
    cur.execute(f"SELECT count(*) FROM {table}")
    return cur.fetchone()[0]


def backup_db(db_path):
    """Create a timestamped backup before merging."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent / f"schools_pre_merge_{timestamp}.db"
    shutil.copy2(str(db_path), str(backup_path))
    size_mb = backup_path.stat().st_size / (1024 * 1024)
    print(f"  ✅ Pre-merge backup: {backup_path.name} ({size_mb:.1f} MB)")
    return backup_path


def verify_merge(conn):
    """Verify merge by comparing school_number sets (src must already be ATTACHed)."""
    print(f"\n  Verification (school_number level):")
    all_ok = True
    for table_info in MERGE_TABLES:
        table = table_info["name"]
        try:
            cur = conn.execute(
                f"SELECT count(DISTINCT school_number) FROM src.{table} "
                f"WHERE school_number NOT IN (SELECT DISTINCT school_number FROM main.{table})"
            )
            missing = cur.fetchone()[0]
            if missing > 0:
                print(f"    ⚠️  {table}: {missing} schools in source but not in target")
                all_ok = False
            else:
                print(f"    ✅ {table}: all source schools present in target")
        except sqlite3.OperationalError as e:
            print(f"    ❌ {table}: verification error — {e}")
            all_ok = False

    # scrape_log row count check
    src_log = count_rows(conn, "src.scrape_log")
    main_log = count_rows(conn, "main.scrape_log")
    if main_log >= src_log:
        print(f"    ✅ scrape_log: target ({main_log}) >= source ({src_log})")
    else:
        print(f"    ⚠️  scrape_log: target ({main_log}) < source ({src_log})")
        all_ok = False

    return all_ok


def merge(source_path, target_path, verify=False):
    """Merge NCEA data from source DB into target DB."""
    source_path = Path(source_path).resolve()
    target_path = Path(target_path).resolve()

    if not source_path.exists():
        print(f"  ❌ Source DB not found: {source_path}")
        sys.exit(1)
    if not target_path.exists():
        print(f"  ❌ Target DB not found: {target_path}")
        sys.exit(1)
    if source_path == target_path:
        print(f"  ❌ Source and target are the same file!")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  NCEA Data Merge")
    print(f"  Source: {source_path}")
    print(f"  Target: {target_path}")
    print(f"{'='*60}\n")

    # Backup target before merge
    backup_db(target_path)

    conn = sqlite3.connect(str(target_path))

    try:
        conn.execute(f"ATTACH '{source_path}' AS src")

        for table_info in MERGE_TABLES:
            table = table_info["name"]
            columns = table_info["columns"]

            before = count_rows(conn, f"main.{table}")
            src_count = count_rows(conn, f"src.{table}")

            conn.execute(
                f"INSERT OR IGNORE INTO main.{table} ({columns}) "
                f"SELECT {columns} FROM src.{table}"
            )

            after = count_rows(conn, f"main.{table}")
            delta = after - before

            print(f"  {table}:")
            print(f"    source: {src_count} | before: {before} | after: {after} | +{delta}")

        if verify:
            ok = verify_merge(conn)
            if not ok:
                conn.rollback()
                conn.execute("DETACH src")
                print(f"\n  ❌ Verification failed — rolling back merge.")
                print(f"  No data was changed. Check source DB for issues.")
                return
            print(f"\n  ✅ Verification passed!")

        conn.commit()
        conn.execute("DETACH src")
        print(f"\n  ✅ Merge complete!")

    except Exception as e:
        conn.rollback()
        print(f"\n  ❌ Merge failed: {e}")
        print(f"  Restore from backup if needed.")
        raise
    finally:
        conn.close()

    print(f"\n{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Merge NCEA data from worktree DB")
    parser.add_argument("--source", required=True, help="Path to worktree (source) DB")
    parser.add_argument("--target", default=str(DEFAULT_TARGET), help="Path to main (target) DB")
    parser.add_argument("--verify", action="store_true", help="Verify merge completeness")
    args = parser.parse_args()

    merge(args.source, args.target, verify=args.verify)


if __name__ == "__main__":
    main()
