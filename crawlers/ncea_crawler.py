#!/usr/bin/env python3
"""
NCEA Performance Data Crawler

Scrapes educationcounts.govt.nz for school performance data:
- Retention (school leavers staying until 17th birthday)
- NCEA Level 1, 2, 3/UE qualifications
- Vocational Pathway Awards

Usage:
    python -m crawlers.ncea_crawler --school 41
    python -m crawlers.ncea_crawler --school 41 --only retention,ncea1
"""

import argparse
import hashlib
import json
import os
import random
import sqlite3
import time
from datetime import datetime
from pathlib import Path

DB_PATH = Path(os.environ.get(
    "SCHOOLS_DB",
    str(Path(__file__).resolve().parent.parent / "schools.db")
))

BASE_URL = "https://www.educationcounts.govt.nz/find-school/school"
METRICS = {
    "retention": "/retention?school={id}",
    "ncea1": "/qualifications/ncea-level-1?school={id}",
    "ncea2": "/qualifications/ncea-level-2?school={id}",
    "ncea3": "/qualifications/ue-standard?school={id}",
    "vocational": "/qualifications/vocational-pathway-awards?school={id}",
}

# Standard group names in table rows
EXPECTED_GROUPS = {"Female", "Male", "Māori", "Pacific", "Asian", "MELAA", "Other", "European/Pākehā", "Total"}


def parse_cell(text):
    """Parse a table cell. Returns (value, is_suppressed).
    'x' = suppressed, 'na' = not applicable, number = value."""
    t = text.strip()
    if t in ("x", "X"):
        return None, True
    if t in ("na", "NA", "n/a", "-", ""):
        return None, False
    try:
        # Handle commas in numbers like "1,234"
        return int(t.replace(",", "")), False
    except ValueError:
        try:
            return float(t.replace(",", "")), False
        except ValueError:
            return None, False


def parse_standard_table(table_data, metric, school_number):
    """Parse a standard performance table (retention, ncea1-3, vocational Table 1).

    Table layout:
      Row 0: Group | Below... (3 year cols) | Above... (3 year cols) | Percentage (3 year cols)
      Row 1:       | 2022 | 2023 | 2024    | 2022 | 2023 | 2024    | 2022 | 2023 | 2024
      Row 2+: data

    So columns are: [group, below_2022, below_2023, below_2024, above_2022, above_2023, above_2024, pct_2022, pct_2023, pct_2024]
    """
    if not table_data or len(table_data) < 3:
        return []

    # Extract years from row 1 (should be [2022, 2023, 2024] repeated 3 times)
    year_row = table_data[1]
    years = []
    for cell in year_row[1:]:
        try:
            years.append(int(cell.strip()))
        except ValueError:
            pass

    # Should have 9 year values (3 metrics x 3 years)
    # Unique years: typically [2022, 2023, 2024]
    unique_years = sorted(set(years))
    n_years = len(unique_years)
    if n_years == 0:
        return []

    rows = []
    for data_row in table_data[2:]:
        if not data_row or not data_row[0]:
            continue
        group = data_row[0].strip()
        if group not in EXPECTED_GROUPS:
            continue

        cells = data_row[1:]
        # Layout: below[0..n-1], above[n..2n-1], pct[2n..3n-1]
        for yi, year in enumerate(unique_years):
            below_idx = yi
            above_idx = n_years + yi
            pct_idx = 2 * n_years + yi

            below_raw = cells[below_idx] if below_idx < len(cells) else ""
            above_raw = cells[above_idx] if above_idx < len(cells) else ""
            pct_raw = cells[pct_idx] if pct_idx < len(cells) else ""

            below_val, below_supp = parse_cell(below_raw)
            above_val, above_supp = parse_cell(above_raw)
            pct_val, pct_supp = parse_cell(pct_raw)

            is_supp = 1 if (below_supp or above_supp or pct_supp) else 0
            raw = f"{below_raw}|{above_raw}|{pct_raw}"

            rows.append((
                school_number, year, metric, group,
                int(below_val) if below_val is not None else None,
                int(above_val) if above_val is not None else None,
                float(pct_val) if pct_val is not None else None,
                is_supp, raw,
            ))

    return rows


def parse_comparison_table(table_data, metric, school_number):
    """Parse comparison table (Table 2). Same column layout as standard table."""
    if not table_data or len(table_data) < 3:
        return []

    year_row = table_data[1]
    years = []
    for cell in year_row[1:]:
        try:
            years.append(int(cell.strip()))
        except ValueError:
            pass

    unique_years = sorted(set(years))
    n_years = len(unique_years)
    if n_years == 0:
        return []

    rows = []
    for data_row in table_data[2:]:
        if not data_row or not data_row[0]:
            continue
        comp_group = data_row[0].strip()
        cells = data_row[1:]

        for yi, year in enumerate(unique_years):
            below_idx = yi
            above_idx = n_years + yi
            pct_idx = 2 * n_years + yi

            below_val, _ = parse_cell(cells[below_idx] if below_idx < len(cells) else "")
            above_val, _ = parse_cell(cells[above_idx] if above_idx < len(cells) else "")
            pct_val, _ = parse_cell(cells[pct_idx] if pct_idx < len(cells) else "")

            rows.append((
                school_number, comp_group, year, metric,
                int(below_val) if below_val is not None else None,
                int(above_val) if above_val is not None else None,
                float(pct_val) if pct_val is not None else None,
            ))

    return rows


def parse_vocational_pathways(table_data, school_number, year=2024):
    """Parse Vocational Table 3 (pathway breakdown by group)."""
    if not table_data or len(table_data) < 2:
        return []

    # Header row has pathway names
    headers = table_data[0]
    # Map header index to pathway code
    pathway_map = {
        "Construction and Infrastructure": "construction",
        "Creative Industries": "creative",
        "Manufacturing and Technology": "manufacturing",
        "Primary Industries": "primary",
        "Service Industries": "service",
        "Social and Community Services": "social",
    }

    rows = []
    for data_row in table_data[1:]:
        if not data_row or not data_row[0]:
            continue
        group = data_row[0].strip()
        if group not in EXPECTED_GROUPS:
            continue

        for ci, cell in enumerate(data_row[1:], 1):
            if ci >= len(headers):
                break
            header = headers[ci].strip()
            pathway = pathway_map.get(header)
            if not pathway:
                if header == "Total Leavers":
                    pathway = "total_leavers"
                else:
                    continue

            val, is_supp = parse_cell(cell)
            rows.append((
                school_number, year, group, pathway,
                int(val) if val is not None else None,
                1 if is_supp else 0,
            ))

    return rows


def scrape_school(school_number, only=None, delay_range=(10, 15)):
    """Scrape all NCEA performance data for a school."""
    from playwright.sync_api import sync_playwright

    metrics_to_scrape = only or list(METRICS.keys())
    results = {"performance": [], "comparison": [], "vocational": []}
    logs = []

    print(f"\n{'='*60}")
    print(f"  NCEA Crawler: School #{school_number}")
    print(f"  Metrics: {', '.join(metrics_to_scrape)}")
    print(f"{'='*60}\n")

    p = sync_playwright().start()
    browser = p.chromium.launch(
        headless=True,
        args=["--disable-blink-features=AutomationControlled"],
    )
    ctx = browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        locale="en-NZ",
        extra_http_headers={
            "Accept-Language": "en-NZ,en;q=0.9",
        },
    )
    page = ctx.new_page()
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

    # Step 1: Visit homepage first to establish cookies
    print("  [0] Visiting Education Counts homepage...")
    try:
        page.goto("https://www.educationcounts.govt.nz/find-school", timeout=30000, wait_until="domcontentloaded")
        time.sleep(random.uniform(3, 5))
    except Exception as e:
        print(f"  [WARN] Homepage visit failed: {e}")

    for i, metric in enumerate(metrics_to_scrape):
        url_path = METRICS[metric].format(id=school_number)
        url = BASE_URL + url_path
        delay = random.uniform(*delay_range)

        print(f"  [{i+1}/{len(metrics_to_scrape)}] {metric} (delay {delay:.0f}s)...")
        time.sleep(delay)

        try:
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            time.sleep(random.uniform(4, 6))  # Wait for JS rendering

            # Extract all tables
            tables = page.evaluate("""() => {
                const tables = document.querySelectorAll('table');
                return Array.from(tables).map(t => {
                    const rows = Array.from(t.querySelectorAll('tr'));
                    return rows.map(r =>
                        Array.from(r.querySelectorAll('th, td')).map(c => c.textContent.trim())
                    );
                });
            }""")

            # Content hash for provenance
            page_text = page.inner_text("body")
            content_hash = hashlib.md5(page_text.encode()).hexdigest()

            logs.append((school_number, metric, url, datetime.now().isoformat(), 200, content_hash, 1))

            # Validate: expect at least 2 tables
            if len(tables) < 2:
                print(f"      [WARN] Expected >=2 tables, got {len(tables)}")
                logs[-1] = (school_number, metric, url, datetime.now().isoformat(), 200, content_hash, 0)
                continue

            # Table 1: School performance data
            perf_rows = parse_standard_table(tables[0], metric, school_number)
            results["performance"].extend(perf_rows)
            print(f"      Table 1: {len(perf_rows)} rows")

            # Table 2: Comparison data
            comp_rows = parse_comparison_table(tables[1], metric, school_number)
            results["comparison"].extend(comp_rows)
            print(f"      Table 2: {len(comp_rows)} comparison rows")

            # Vocational Table 3 (only for vocational metric)
            if metric == "vocational" and len(tables) >= 3:
                voc_rows = parse_vocational_pathways(tables[2], school_number)
                results["vocational"].extend(voc_rows)
                print(f"      Table 3: {len(voc_rows)} vocational pathway rows")

            # Validate: Total row should exist
            total_rows = [r for r in perf_rows if r[3] == "Total"]
            if not total_rows:
                print(f"      [WARN] No 'Total' row found in {metric}")

        except Exception as e:
            print(f"      [ERROR] {e}")
            logs.append((school_number, metric, url, datetime.now().isoformat(), 0, "", 0))

    browser.close()
    p.stop()

    # Write to database
    print(f"\n  Writing to database...")
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    try:
        # Performance data
        for row in results["performance"]:
            cur.execute(
                "INSERT OR REPLACE INTO school_performance "
                "(school_number, year, metric, group_name, below_count, above_count, percentage, is_suppressed, raw_value) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", row
            )
        print(f"  ✅ school_performance: {len(results['performance'])} rows")

        # Comparison data
        for row in results["comparison"]:
            cur.execute(
                "INSERT OR REPLACE INTO school_performance_comparison "
                "(school_number, comparison_group, year, metric, below_count, above_count, percentage) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)", row
            )
        print(f"  ✅ comparison: {len(results['comparison'])} rows")

        # Vocational pathways
        for row in results["vocational"]:
            cur.execute(
                "INSERT OR REPLACE INTO school_vocational_pathways "
                "(school_number, year, group_name, pathway, count, is_suppressed) "
                "VALUES (?, ?, ?, ?, ?, ?)", row
            )
        print(f"  ✅ vocational_pathways: {len(results['vocational'])} rows")

        # Scrape logs
        for log in logs:
            cur.execute(
                "INSERT INTO scrape_log (school_number, metric, source_url, scraped_at, http_status, content_hash, success) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)", log
            )
        print(f"  ✅ scrape_log: {len(logs)} entries")

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"  ❌ Database error: {e}")
        raise
    finally:
        conn.close()

    # Summary
    total = len(results["performance"])
    success = sum(1 for l in logs if l[6] == 1)
    print(f"\n{'='*60}")
    print(f"  NCEA Crawl Complete: School #{school_number}")
    print(f"  Metrics scraped: {success}/{len(metrics_to_scrape)}")
    print(f"  Performance rows: {len(results['performance'])}")
    print(f"  Comparison rows: {len(results['comparison'])}")
    print(f"  Vocational rows: {len(results['vocational'])}")
    print(f"{'='*60}\n")

    return results


def main():
    parser = argparse.ArgumentParser(description="NCEA Performance Data Crawler")
    parser.add_argument("--school", type=int, required=True, help="School number")
    parser.add_argument("--only", help="Comma-separated metrics to scrape (retention,ncea1,ncea2,ncea3,vocational)")
    parser.add_argument("--delay-min", type=int, default=10, help="Min delay between pages (seconds)")
    parser.add_argument("--delay-max", type=int, default=15, help="Max delay between pages (seconds)")
    args = parser.parse_args()

    only = [m.strip() for m in args.only.split(",")] if args.only else None
    scrape_school(args.school, only=only, delay_range=(args.delay_min, args.delay_max))


if __name__ == "__main__":
    main()

# TODO: add circuit breaker - stop after 2 consecutive 403s
