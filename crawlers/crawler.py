#!/usr/bin/env python3
"""
NZ School Finder — Crawler Pipeline Entry Point

Usage:
    # Crawl a single school
    python -m crawlers.crawler --school 41

    # List available school crawlers
    python -m crawlers.crawler --list

    # Commit reviewed data to database
    python -m crawlers.crawler --commit 41 --status approved
"""

import argparse
import importlib
import sys
from pathlib import Path

from .templates.base import CrawlStatus, commit_to_db


SCHOOLS_DIR = Path(__file__).parent / "schools"


def find_school_crawler(school_number: int):
    """Find and instantiate the crawler for a given school number."""
    # Look for crawlers/schools/school_{num}_*.py
    pattern = f"school_{school_number}_*.py"
    matches = list(SCHOOLS_DIR.glob(pattern))

    if not matches:
        print(f"No crawler found for school #{school_number}")
        print(f"Expected file: crawlers/schools/school_{school_number}_<name>.py")
        print(f"\nAvailable crawlers:")
        list_crawlers()
        return None

    # Import the module
    module_name = matches[0].stem  # e.g. "school_41_macleans"
    module = importlib.import_module(f"crawlers.schools.{module_name}")

    # Find the crawler class — must be a direct subclass defined in this module
    from .templates.base import BaseCrawler
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if (
            isinstance(attr, type)
            and issubclass(attr, BaseCrawler)
            and attr.__module__ == module.__name__
        ):
            return attr(school_number)

    print(f"No crawler class found in {matches[0]}")
    return None


def list_crawlers():
    """List all available per-school crawlers."""
    scripts = sorted(SCHOOLS_DIR.glob("school_*.py"))
    if not scripts:
        print("  (none — create scripts in crawlers/schools/)")
        return
    for script in scripts:
        name = script.stem
        parts = name.split("_", 2)  # school_41_macleans
        num = parts[1] if len(parts) > 1 else "?"
        label = parts[2].replace("_", " ").title() if len(parts) > 2 else ""
        print(f"  #{num}: {label} ({script.name})")


def main():
    parser = argparse.ArgumentParser(
        description="NZ School Finder Crawler",
        epilog="Parts: subjects, sports, arts, clubs, fees, curriculum, zone, logo",
    )
    parser.add_argument("--school", type=int, help="School number to crawl")
    parser.add_argument(
        "--only",
        help="Only extract these parts (comma-separated). E.g. --only subjects,fees",
    )
    parser.add_argument("--list", action="store_true", help="List available crawlers")
    parser.add_argument("--parts", action="store_true", help="List extractable parts")
    parser.add_argument("--commit", type=int, help="Commit reviewed data for school number")
    parser.add_argument(
        "--status",
        choices=["approved", "partial"],
        default="approved",
        help="Commit status (default: approved)",
    )
    args = parser.parse_args()

    if args.list:
        print("Available school crawlers:")
        list_crawlers()
        return

    if args.parts:
        from .templates.base import BaseCrawler
        print("Extractable parts:")
        for p in BaseCrawler.EXTRACT_PARTS:
            print(f"  - {p}")
        print(f"\nUsage: python -m crawlers.crawler --school 41 --only subjects,fees")
        return

    if args.commit:
        # Load the latest log and commit — requires review report to exist
        from .templates.base import LOG_DIR
        import json

        # Check review report exists (human must have reviewed)
        review_files = sorted(LOG_DIR.glob(f"review_{args.commit}_*.md"), reverse=True)
        if not review_files:
            print(f"❌ No review report found for school #{args.commit}")
            print(f"   Run the crawler first (--school {args.commit}), then review the report.")
            sys.exit(1)
        print(f"  Review report found: {review_files[0].name}")

        log_files = sorted(LOG_DIR.glob(f"school_{args.commit}_*.json"), reverse=True)
        if not log_files:
            print(f"No crawl log found for school #{args.commit}")
            sys.exit(1)

        latest_log = log_files[0]
        print(f"Committing from: {latest_log}")
        with open(latest_log, encoding="utf-8") as f:
            log_data = json.load(f)

        # Reconstruct SchoolData from log
        from .templates.base import SchoolData
        data = SchoolData(log_data["school_number"], log_data["school_name"])
        data.subjects = log_data.get("subjects_raw", [])
        data.subjects_url = log_data.get("subjects_url", "")
        data.sports = log_data.get("sports", [])
        data.sports_url = log_data.get("sports_url", "")
        data.arts = log_data.get("arts", [])
        data.arts_url = log_data.get("arts_url", "")
        data.clubs = log_data.get("clubs", [])
        data.clubs_url = log_data.get("clubs_url", "")
        data.intl_tuition_annual = log_data.get("intl_tuition_annual")
        data.intl_homestay_weekly = log_data.get("intl_homestay_weekly")
        data.intl_fees_url = log_data.get("intl_fees_url", "")
        data.curriculum_systems = log_data.get("curriculum_systems", [])
        data.zone_map_url = log_data.get("zone_map_url", "")
        data.zone_streets_url = log_data.get("zone_streets_url", "")
        data.zone_page_url = log_data.get("zone_page_url", "")
        data.logo_url = log_data.get("logo_url", "")
        data.crawled_at = log_data.get("crawled_at", "")

        status = CrawlStatus.APPROVED if args.status == "approved" else CrawlStatus.PARTIAL
        commit_to_db(data, status)
        return

    if args.school:
        crawler = find_school_crawler(args.school)
        if crawler:
            only = [p.strip() for p in args.only.split(",")] if args.only else None
            crawler.crawl(only=only)
        else:
            sys.exit(1)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
