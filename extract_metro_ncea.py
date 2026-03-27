#!/usr/bin/env python3
"""
Extract NCEA data from Metro Schools 2025 PDF and import into SQLite.

Usage: python extract_metro_ncea.py [--dry-run]

Source: met447_schoolsDataONLY_212x277.pdf
Data year: 2023 NCEA results
"""

import sys
import os
import re
import json
import hashlib
import sqlite3
from datetime import datetime

try:
    import fitz  # PyMuPDF
except ImportError:
    print("ERROR: PyMuPDF not installed. Run: pip install PyMuPDF")
    sys.exit(1)

# ─── Configuration ───────────────────────────────────────────────────

PDF_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "met447_schoolsDataONLY_212x277.pdf")
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schools.db")
EXPECTED_MD5 = "051ee7181b53b6c77870aacc4dabd304"
DATA_YEAR = 2023
SOURCE = "metro_2025"

# Core table pages (0-indexed)
CORE_PAGES = [30, 31, 32]  # PDF pages 31-33

# Known region headers in PDF (Local Board Areas)
KNOWN_REGIONS = {
    "Albert-Eden", "Devonport-Takapuna", "Franklin", "Henderson-Massey",
    "Hibiscus and Bays", "Howick", "Kaipātiki", "Māngere-Ōtāhuhu",
    "Manurewa", "Maungakiekie-Tāmaki", "Ōrākei", "Ōtara-Papatoetoe",
    "Papakura", "Puketāpapa", "Rodney", "Upper Harbour", "Waiheke",
    "Waitematā", "Whau",
}
# Subject Top10 pages (0-indexed)
SUBJECT_PAGES = [6, 7, 8]  # PDF pages 7-9

# Subject names in order they appear in PDF (pages 7-9)
SUBJECT_ORDER = [
    "Engineering and Manufacturing",
    "Field Māori",
    "Health and Physical Education",
    "English and Communication Skills",
    "Languages",
    "Sciences",
    "Mathematics and Statistics",
    "Social Sciences",
    "Te Reo Māori",
    "Technology",
    "The Arts",
]

# Known name differences: PDF name → DB name
MAPPING = {
    "Auckland Seventh-Day Adventist H S": "Auckland Seventh-Day Adventist High School",
    "Diocesan School For Girls": "Diocesan School for Girls",
    "Mount Albert Grammar School": "Mt Albert Grammar School",
    "Mount Roskill Grammar": "Mt Roskill Grammar",
    "Waitākere College": "Waitakere College",
    "Whangaparāoa College": "Whangaparaoa College",
    "Māngere College": "Mangere College",
    "Tāmaki College": "Tamaki College",
    "Sir Edmund Hillary Collegiate Senior School": "Sir Edmund Hillary Collegiate Senior School",
    "Western Springs College-Ngā Puna o Waiōrea": "Western Springs College",
}

# Known non-Auckland or non-matching schools in Top10 that can be safely skipped
RANKING_SKIP_ALLOWLIST = set()

# Golden data assertions (for validation)
GOLDEN_DATA = {
    "Auckland Grammar School": {
        "ue_percentage": 74.0,
        "school_leavers": 484,
        "school_roll_july2024": 2696,
        "below_l1_pct": 5.0,
        "l1_pct": 5.0,
        "l2_pct": 13.0,
        "l3_pct": 3.0,
        "scholarships": 22.0,
        "outstanding_merit": 3.0,
        "distinction": 26.0,
    },
    "Macleans College": {
        "ue_percentage": 78.0,
        "school_leavers": 492,
        "school_roll_july2024": 2902,
    },
    "St Cuthbert\u2019s College (Epsom)": {
        "ue_percentage": 94.0,
        "school_leavers": 153,
    },
}


# ─── PDF Checksum ────────────────────────────────────────────────────

def verify_checksum(path):
    """Verify PDF MD5 checksum."""
    with open(path, "rb") as f:
        md5 = hashlib.md5(f.read()).hexdigest()
    if md5 != EXPECTED_MD5:
        print(f"ERROR: PDF checksum mismatch!")
        print(f"  Expected: {EXPECTED_MD5}")
        print(f"  Got:      {md5}")
        return False, md5
    return True, md5


# ─── Core Table Extraction (Pages 31-33) ─────────────────────────────

def extract_core_table(doc):
    """Extract school data from pages 31-33."""
    schools = []
    current_region = None

    for page_idx in CORE_PAGES:
        page = doc[page_idx]
        lines = page.get_text().split("\n")

        i = 0
        # Skip header lines (page title + column headers)
        while i < len(lines):
            line = lines[i].strip()
            if line in ("Schools", "Results", "School Name", ""):
                i += 1
                continue
            if line.startswith("School Roll") or line.startswith("(July") or \
               line.startswith("School ") or line.startswith("Leavers") or \
               line.startswith("(2023") or line.startswith("University") or \
               line.startswith("Entrance") or line.startswith("achieving") or \
               line.startswith("Level ") or line.startswith("Scholarships") or \
               line.startswith("Presented") or line.startswith("Students with") or \
               line.startswith("Outstanding") or line.startswith("Merit") or \
               line.startswith("Distinction") or line.startswith("Leavers not"):
                i += 1
                continue
            break

        # Header lines to skip — match after strip()
        HEADER_SKIP = {"Schools", "Results", "School Name", "School Roll",
                        "(July 2024)", "School", "Leavers", "(2023)",
                        "University", "Entrance", "achieving",
                        "Level 1 (%)", "Level 2 (%)", "Level 3 (%)",
                        "Leavers not", "Scholarships", "Presented",
                        "Students with", "Outstanding", "Merit", "Distinction"}

        def is_header_line(text):
            """Check if a stripped line is a page/column header (not a school name)."""
            # School names contain multiple words and don't match exact header keywords
            return text in HEADER_SKIP

        while i < len(lines):
            line = lines[i].strip()
            if not line or is_header_line(line):
                i += 1
                continue

            # Check if this is a known region header
            if line in KNOWN_REGIONS:
                current_region = line
                i += 1
                continue

            # This is a school name — may be multi-line
            # Collect name lines until we hit a numeric value
            name_parts = [line]
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                if not next_line:
                    i += 1
                    continue
                next_clean = next_line.replace(' ', '')
                if re.match(r'^[\d,]+$', next_clean) or re.match(r'^\d+%$', next_clean):
                    break
                # Check if it's a region header or page header
                if next_line in KNOWN_REGIONS:
                    break
                name_parts.append(next_line)
                i += 1

            school_name = " ".join(name_parts)
            school_name = re.sub(r'\s+', ' ', school_name).strip()

            # Collect 10 numeric values:
            # roll(int), leavers(int), ue%, below_l1%, l1%, l2%, l3%, scholarships%, merit%, distinction%
            values = []
            while i < len(lines) and len(values) < 10:
                val_line = lines[i].strip()
                if not val_line:
                    i += 1
                    continue

                val_line_clean = val_line.replace(' ', '')
                if re.match(r'^[\d,]+$', val_line_clean):
                    values.append(int(val_line_clean.replace(',', '')))
                    i += 1
                elif re.match(r'^\d+%$', val_line_clean):
                    values.append(int(val_line_clean.replace('%', '')))
                    i += 1
                else:
                    break

            if len(values) == 10:
                school = {
                    "school_name": school_name,
                    "region": current_region,
                    "school_roll_july2024": values[0],
                    "school_leavers": values[1],
                    "ue_percentage": float(values[2]),
                    "below_l1_pct": float(values[3]),
                    "l1_pct": float(values[4]),
                    "l2_pct": float(values[5]),
                    "l3_pct": float(values[6]),
                    "scholarships": float(values[7]),       # percentage, not count
                    "outstanding_merit": float(values[8]),
                    "distinction": float(values[9]),
                }
                schools.append(school)
            else:
                # Could not parse 8 values — this is an error
                print(f"  ERROR: Could not parse school '{school_name}' "
                      f"(got {len(values)} values: {values})")
                print(f"  → This is unexpected. Check PDF text extraction.")
                sys.exit(1)

    return schools


# ─── Subject Top10 Extraction (Pages 7-9) ────────────────────────────

def extract_subject_rankings(doc):
    """Extract subject Top10 rankings from pages 7-9."""
    rankings = []
    all_lines = []

    for page_idx in SUBJECT_PAGES:
        page = doc[page_idx]
        all_lines.extend(page.get_text().split("\n"))

    # Find all ranking blocks: each starts with "RANK" / "SCHOOL" / "LEVEL 3%"
    # then 10 entries of: rank_number / school_name / percentage
    subject_idx = 0
    i = 0

    while i < len(all_lines):
        line = all_lines[i].strip()
        if line == "RANK":
            # Check if next lines are SCHOOL and LEVEL 3%
            if (i + 2 < len(all_lines) and
                all_lines[i + 1].strip() == "SCHOOL" and
                all_lines[i + 2].strip() == "LEVEL 3%"):
                i += 3  # skip header

                if subject_idx >= len(SUBJECT_ORDER):
                    print(f"  WARNING: Found more than {len(SUBJECT_ORDER)} subject blocks")
                    break

                subject_name = SUBJECT_ORDER[subject_idx]
                entries = []

                while i < len(all_lines) and len(entries) < 10:
                    rank_line = all_lines[i].strip()
                    if not rank_line or not re.match(r'^\d+$', rank_line):
                        break
                    rank = int(rank_line)
                    i += 1

                    # School name (might be multi-line)
                    school_name = all_lines[i].strip() if i < len(all_lines) else ""
                    i += 1

                    # Check if next line is percentage or continuation of name
                    if i < len(all_lines):
                        next_line = all_lines[i].strip()
                        if not re.match(r'^\d+\.\d+%$', next_line):
                            # Multi-line school name
                            school_name += " " + next_line
                            i += 1

                    # Percentage
                    if i < len(all_lines):
                        pct_line = all_lines[i].strip()
                        pct_match = re.match(r'^(\d+\.\d+)%$', pct_line)
                        if pct_match:
                            level3_pct = float(pct_match.group(1))
                            entries.append({
                                "subject": subject_name,
                                "school_name": school_name,
                                "rank": rank,
                                "level3_pct": level3_pct,
                            })
                            i += 1
                        else:
                            print(f"  WARNING: Expected percentage, got '{pct_line}' "
                                  f"for {subject_name} rank {rank}")
                            break

                rankings.extend(entries)
                subject_idx += 1
                continue
        i += 1

    return rankings, subject_idx


# ─── School Name Matching ────────────────────────────────────────────

def normalize_name(name):
    """Normalize school name for matching."""
    n = name.strip()
    n = re.sub(r'\s+', ' ', n)
    # Common abbreviations
    n = n.replace(" H S", " High School")
    n = n.replace("St ", "Saint ")
    # Remove punctuation for comparison
    n = re.sub(r"['\u2019\-\u2013]", '', n)
    return n.lower()


def build_school_lookup(db_path):
    """Build lookup dict from schools table: name → school_number."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT school_number, school_name FROM schools")
    rows = cur.fetchall()
    conn.close()

    exact = {}
    normalized = {}
    for num, name in rows:
        exact[name] = num
        nkey = normalize_name(name)
        if nkey in normalized:
            normalized[nkey] = None  # ambiguous
        else:
            normalized[nkey] = num

    return exact, normalized


def match_school(name, exact_lookup, norm_lookup):
    """Match a PDF school name to school_number. Returns (school_number, match_type) or (None, None)."""
    # 1. Check MAPPING first
    if name in MAPPING:
        mapped_name = MAPPING[name]
        if mapped_name in exact_lookup:
            return exact_lookup[mapped_name], "mapping"

    # 2. Exact match
    if name in exact_lookup:
        return exact_lookup[name], "exact"

    # 3. Normalized match
    nkey = normalize_name(name)
    num = norm_lookup.get(nkey)
    if num is not None:
        return num, "normalized"
    if num is None and nkey in norm_lookup:
        return None, "ambiguous"

    return None, None


# ─── Validation ──────────────────────────────────────────────────────

def validate_core_data(schools):
    """Validate extracted core data. Returns (ok, errors)."""
    errors = []

    for s in schools:
        name = s["school_name"]

        # Percentage range checks
        for field in ["ue_percentage", "below_l1_pct", "l1_pct", "l2_pct", "l3_pct"]:
            val = s.get(field)
            if val is not None and (val < 0 or val > 100):
                errors.append(f"[{name}] {field}={val} out of range [0,100]")

        for field in ["outstanding_merit", "distinction"]:
            val = s.get(field)
            if val is not None and (val < 0 or val > 100):
                errors.append(f"[{name}] {field}={val} out of range [0,100]")

        # Distribution cross-check: below_l1 + l1 + l2 + l3 ≈ 100 (±2)
        dist_sum = (s["below_l1_pct"] + s["l1_pct"] + s["l2_pct"] + s["l3_pct"])
        # Note: l3_pct in PDF includes UE students. The actual distribution is:
        # below_l1 + l1 + l2 + (l3 which is NOT UE portion + UE portion)
        # but in the PDF, l3_pct is already the "achieving Level 3" which may NOT include UE
        # Let's check: below_l1 + l1 + l2 + l3 + ue should ≈ 100
        # Actually from data: Auckland Grammar: 5+5+13+3 = 26, UE=74, total=100 ✓
        # So l3_pct here means "achieved L3 but NOT UE"
        total = dist_sum + s["ue_percentage"]
        if total < 98 or total > 102:
            errors.append(f"[{name}] distribution sum={total} (expected ~100)")

    # Duplicate check
    names = [s["school_name"] for s in schools]
    if len(names) != len(set(names)):
        dupes = [n for n in names if names.count(n) > 1]
        errors.append(f"Duplicate schools: {set(dupes)}")

    # Golden data assertions
    school_by_name = {s["school_name"]: s for s in schools}
    for golden_name, expected in GOLDEN_DATA.items():
        if golden_name not in school_by_name:
            errors.append(f"Golden school '{golden_name}' not found in extracted data")
            continue
        actual = school_by_name[golden_name]
        for field, exp_val in expected.items():
            act_val = actual.get(field)
            if act_val != exp_val:
                errors.append(f"Golden [{golden_name}].{field}: expected {exp_val}, got {act_val}")

    return len(errors) == 0, errors


def validate_rankings(rankings, subject_count):
    """Validate extracted subject rankings."""
    errors = []

    if subject_count != len(SUBJECT_ORDER):
        errors.append(f"Expected {len(SUBJECT_ORDER)} subjects, found {subject_count}")

    # Check each subject has entries
    subjects_found = set()
    for r in rankings:
        subjects_found.add(r["subject"])

    for expected_subj in SUBJECT_ORDER:
        if expected_subj not in subjects_found:
            errors.append(f"Missing subject: {expected_subj}")

    # Check rank continuity per subject
    by_subject = {}
    for r in rankings:
        by_subject.setdefault(r["subject"], []).append(r["rank"])

    for subj, ranks in by_subject.items():
        sorted_ranks = sorted(ranks)
        if sorted_ranks[0] != 1:
            errors.append(f"[{subj}] First rank is {sorted_ranks[0]}, expected 1")
        if len(sorted_ranks) < 8:
            errors.append(f"[{subj}] Only {len(sorted_ranks)} entries, expected ≥8")
        # Check continuity
        for j in range(1, len(sorted_ranks)):
            if sorted_ranks[j] != sorted_ranks[j - 1] + 1:
                errors.append(f"[{subj}] Non-continuous ranks: {sorted_ranks}")
                break

    return len(errors) == 0, errors


# ─── Database Import ─────────────────────────────────────────────────

def create_tables(conn):
    """Create NCEA tables if not exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS school_ncea_summary (
            school_number        INTEGER NOT NULL,
            data_year            INTEGER NOT NULL,
            source               TEXT DEFAULT 'metro_2025',
            school_roll_july2024 INTEGER,
            school_leavers       INTEGER,
            ue_percentage        REAL,
            below_l1_pct         REAL,
            l1_pct               REAL,
            l2_pct               REAL,
            l3_pct               REAL,
            scholarships         REAL,
            outstanding_merit    REAL,
            distinction          REAL,
            region               TEXT,
            import_checksum      TEXT,
            imported_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (school_number, data_year)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS school_subject_ranking (
            school_number     INTEGER NOT NULL,
            data_year         INTEGER NOT NULL,
            subject           TEXT NOT NULL,
            rank              INTEGER,
            level3_pct        REAL,
            source            TEXT DEFAULT 'metro_2025',
            PRIMARY KEY (school_number, data_year, subject)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ncea_summary_year ON school_ncea_summary(data_year)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_subject_ranking_subject ON school_subject_ranking(subject, data_year)")


def import_data(conn, schools_matched, rankings_matched, checksum, dry_run=False):
    """Import data into SQLite with transaction."""
    if dry_run:
        print("\n[DRY RUN] Would import:")
        print(f"  {len(schools_matched)} schools to school_ncea_summary")
        print(f"  {len(rankings_matched)} rankings to school_subject_ranking")
        return True

    try:
        # Delete existing data for this source+year (idempotent)
        conn.execute("DELETE FROM school_ncea_summary WHERE source=? AND data_year=?",
                      (SOURCE, DATA_YEAR))
        conn.execute("DELETE FROM school_subject_ranking WHERE source=? AND data_year=?",
                      (SOURCE, DATA_YEAR))

        # Insert core data
        for s in schools_matched:
            conn.execute("""
                INSERT OR REPLACE INTO school_ncea_summary
                (school_number, data_year, source, school_roll_july2024, school_leavers,
                 ue_percentage, below_l1_pct, l1_pct, l2_pct, l3_pct,
                 scholarships, outstanding_merit, distinction, region,
                 import_checksum, imported_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                s["school_number"], DATA_YEAR, SOURCE,
                s["school_roll_july2024"], s["school_leavers"],
                s["ue_percentage"], s["below_l1_pct"], s["l1_pct"],
                s["l2_pct"], s["l3_pct"], s["scholarships"],
                s["outstanding_merit"], s["distinction"], s["region"],
                checksum, datetime.now().isoformat(),
            ))

        # Insert rankings
        for r in rankings_matched:
            conn.execute("""
                INSERT OR REPLACE INTO school_subject_ranking
                (school_number, data_year, subject, rank, level3_pct, source)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                r["school_number"], DATA_YEAR, r["subject"],
                r["rank"], r["level3_pct"], SOURCE,
            ))

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"ERROR: Import failed, rolled back: {e}")
        return False


# ─── Main ────────────────────────────────────────────────────────────

def main():
    dry_run = "--dry-run" in sys.argv

    print("=" * 60)
    print("Metro Schools 2025 — NCEA Data Extraction")
    print("=" * 60)

    # Step 1: Verify PDF
    if not os.path.exists(PDF_PATH):
        print(f"ERROR: PDF not found at {PDF_PATH}")
        sys.exit(1)

    ok, checksum = verify_checksum(PDF_PATH)
    if not ok:
        sys.exit(1)
    print(f"✓ PDF checksum verified: {checksum}")

    # Step 2: Extract core table
    print("\n--- Extracting core table (pages 31-33) ---")
    doc = fitz.open(PDF_PATH)
    schools = extract_core_table(doc)
    print(f"  Extracted {len(schools)} schools")

    # Step 3: Extract subject rankings
    print("\n--- Extracting subject Top 10 (pages 7-9) ---")
    rankings, subject_count = extract_subject_rankings(doc)
    print(f"  Extracted {len(rankings)} ranking entries across {subject_count} subjects")
    doc.close()

    # Step 4: Validate extracted data
    print("\n--- Validating extracted data ---")
    ok_core, errors_core = validate_core_data(schools)
    if not ok_core:
        print("  CORE TABLE VALIDATION ERRORS:")
        for e in errors_core:
            print(f"    ✗ {e}")
        sys.exit(1)
    print(f"  ✓ Core table validation passed ({len(schools)} schools)")

    ok_rank, errors_rank = validate_rankings(rankings, subject_count)
    if not ok_rank:
        print("  RANKING VALIDATION ERRORS:")
        for e in errors_rank:
            print(f"    ✗ {e}")
        sys.exit(1)
    print(f"  ✓ Rankings validation passed ({len(rankings)} entries, {subject_count} subjects)")

    # Step 5: Match school names
    print("\n--- Matching school names ---")
    exact_lookup, norm_lookup = build_school_lookup(DB_PATH)

    # Match core table schools
    unmatched = []
    schools_matched = []
    match_stats = {"exact": 0, "normalized": 0, "mapping": 0}

    for s in schools:
        num, match_type = match_school(s["school_name"], exact_lookup, norm_lookup)
        if num is not None:
            s["school_number"] = int(num)
            schools_matched.append(s)
            match_stats[match_type] = match_stats.get(match_type, 0) + 1
        else:
            unmatched.append({"school_name": s["school_name"], "region": s["region"],
                              "match_result": match_type or "not_found"})

    print(f"  Matched: {len(schools_matched)} "
          f"(exact={match_stats['exact']}, normalized={match_stats['normalized']}, "
          f"mapping={match_stats['mapping']})")

    if unmatched:
        unmatched_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       "unmatched_schools.json")
        with open(unmatched_path, "w") as f:
            json.dump(unmatched, f, indent=2, ensure_ascii=False)
        print(f"\n  ✗ {len(unmatched)} UNMATCHED schools:")
        for u in unmatched:
            print(f"    - {u['school_name']} ({u['region']}) [{u['match_result']}]")
        print(f"\n  Written to: {unmatched_path}")
        print("  → Add entries to MAPPING dict in this script and re-run.")
        sys.exit(1)

    # Match ranking schools
    rankings_matched = []
    ranking_skipped = []

    # Build set of matched school_numbers for cross-table check
    summary_school_numbers = {s["school_number"] for s in schools_matched}

    for r in rankings:
        num, match_type = match_school(r["school_name"], exact_lookup, norm_lookup)
        if num is not None:
            if int(num) in summary_school_numbers:
                r["school_number"] = int(num)
                rankings_matched.append(r)
            else:
                # Matched to DB but not in summary → treat as skip
                ranking_skipped.append(r["school_name"])
        elif r["school_name"] in RANKING_SKIP_ALLOWLIST:
            ranking_skipped.append(r["school_name"])
        else:
            print(f"\n  ✗ Ranking school not matched and not in allowlist: '{r['school_name']}'")
            print("  → Add to MAPPING dict or RANKING_SKIP_ALLOWLIST and re-run.")
            sys.exit(1)

    print(f"  Rankings matched: {len(rankings_matched)}, skipped: {len(ranking_skipped)}")
    if ranking_skipped:
        print(f"    Skipped: {set(ranking_skipped)}")

    # Step 6: Import to database
    print("\n--- Importing to database ---")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    create_tables(conn)

    ok = import_data(conn, schools_matched, rankings_matched, checksum, dry_run)
    conn.close()

    if not ok:
        sys.exit(1)

    # Step 7: Report
    print("\n" + "=" * 60)
    print("  IMPORT REPORT")
    print("=" * 60)
    print(f"  Source:          Metro Schools 2025 PDF")
    print(f"  Data year:       {DATA_YEAR}")
    print(f"  PDF checksum:    {checksum}")
    if dry_run:
        print(f"  Mode:            DRY RUN (no data written)")
    else:
        print(f"  Mode:            LIVE IMPORT")
    print(f"  Schools imported: {len(schools_matched)}")
    print(f"  Rankings imported: {len(rankings_matched)}")
    print(f"  Rankings skipped: {len(ranking_skipped)}")
    print(f"  Match stats:     {match_stats}")
    print("=" * 60)
    print("  ✓ Done!")


if __name__ == "__main__":
    main()
