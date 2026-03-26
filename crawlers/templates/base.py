"""
Base crawler template — all site-type templates inherit from this.

Pipeline: discover pages → fetch content → extract data → validate → generate review report
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional


# ── Constants ─────────────────────────────────────────

DB_PATH = Path(__file__).resolve().parent.parent.parent / "schools.db"
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
RATE_LIMIT_SECONDS = 2


# ── Crawl status enum ────────────────────────────────

class CrawlStatus:
    """
    Canonical state lifecycle:
      PENDING → (crawl) → CRAWLED → (human review) → APPROVED / PARTIAL / REJECTED / BLOCKED

    Terminal states:
      APPROVED  — all required modules meet thresholds, reviewer confirmed
      PARTIAL   — some data available but below thresholds or missing modules
      REJECTED  — reviewer decided data is unusable, needs re-crawl
      BLOCKED   — cannot crawl (no website, anti-bot, login wall, permanent failure)
    """
    PENDING = "PENDING"
    CRAWLED = "CRAWLED"       # fetched, awaiting human review
    APPROVED = "APPROVED"     # reviewed and committed to DB
    PARTIAL = "PARTIAL"       # some fields missing but usable
    REJECTED = "REJECTED"     # reviewer rejected, needs re-crawl or manual fix
    BLOCKED = "BLOCKED"       # cannot crawl (no site, anti-bot, login wall)


# ── Extracted data container ─────────────────────────

class SchoolData:
    """Container for all data extracted from a school website."""

    def __init__(self, school_number: int, school_name: str):
        self.school_number = school_number
        self.school_name = school_name

        # Subjects (matched against subject_pool)
        self.subjects: list[dict] = []       # [{name, raw_name, confidence, source_url}]
        self.subjects_url: str = ""

        # Sports
        self.sports: list[str] = []
        self.sports_url: str = ""

        # Arts / Performing Arts (music, drama, Kapa Haka)
        self.arts: list[str] = []
        self.arts_url: str = ""

        # Clubs (non-sports, non-arts extracurricular)
        self.clubs: list[str] = []
        self.clubs_url: str = ""

        # International fees
        self.intl_tuition_annual: float | None = None
        self.intl_homestay_weekly: float | None = None
        self.intl_fees_url: str = ""
        self.intl_fees_year: int | None = None  # e.g. 2026

        # Curriculum systems
        self.curriculum_systems: list[dict] = []  # [{system, status, evidence_url}]

        # Zone
        self.zone_map_url: str = ""
        self.zone_streets_url: str = ""
        self.zone_page_url: str = ""

        # Logo
        self.logo_url: str = ""

        # Metadata
        self.site_type: str = ""          # wordpress / wix / standard_html / etc.
        self.pages_crawled: list[str] = []
        self.warnings: list[str] = []     # issues found during extraction
        self.crawled_at: str = ""

    def to_dict(self) -> dict:
        return {
            "school_number": self.school_number,
            "school_name": self.school_name,
            "subjects": [s["name"] for s in self.subjects],
            "subjects_raw": self.subjects,
            "subjects_url": self.subjects_url,
            "subjects_count": len(self.subjects),
            "sports": self.sports,
            "sports_url": self.sports_url,
            "sports_count": len(self.sports),
            "arts": self.arts,
            "arts_url": self.arts_url,
            "arts_count": len(self.arts),
            "clubs": self.clubs,
            "clubs_url": self.clubs_url,
            "clubs_count": len(self.clubs),
            "intl_tuition_annual": self.intl_tuition_annual,
            "intl_homestay_weekly": self.intl_homestay_weekly,
            "intl_fees_url": self.intl_fees_url,
            "intl_fees_year": self.intl_fees_year,
            "curriculum_systems": self.curriculum_systems,
            "zone_map_url": self.zone_map_url,
            "zone_streets_url": self.zone_streets_url,
            "zone_page_url": self.zone_page_url,
            "logo_url": self.logo_url,
            "site_type": self.site_type,
            "pages_crawled": self.pages_crawled,
            "warnings": self.warnings,
            "crawled_at": self.crawled_at,
        }


# ── Base crawler ─────────────────────────────────────

class BaseCrawler(ABC):
    """
    Base class for all school crawlers.

    Subclasses must implement:
      - discover_pages(): find relevant pages on the school website
      - extract_subjects(): extract subject data
      - extract_sports(): extract sports data
      - extract_music(): extract music/performing arts data
      - extract_activities(): extract activities/clubs data
      - extract_fees(): extract international fees
      - extract_curriculum(): extract curriculum systems (NCEA/IB/etc.)

    Optional overrides:
      - extract_logo(): find school logo URL
      - extract_zone(): find zone/enrolment info
    """

    SITE_TYPE = "unknown"

    def __init__(self, school_number: int):
        self.school_number = school_number
        self.school_name = ""
        self.website = ""
        self.data = None
        self._pages: dict[str, str] = {}  # url -> content cache

        # Load school info from DB
        self._load_school_info()

    def _load_school_info(self):
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            "SELECT school_name, school_website FROM schools WHERE school_number = ?",
            (str(self.school_number),),
        )
        row = cur.fetchone()
        conn.close()
        if not row:
            raise ValueError(f"School {self.school_number} not found in database")
        self.school_name = row["school_name"]
        self.website = row["school_website"] or ""

    # ── Fetching ─────────────────────────────────────

    def fetch_page(self, url: str) -> str:
        """Fetch a page and return its text content. Respects rate limiting."""
        if url in self._pages:
            return self._pages[url]

        time.sleep(RATE_LIMIT_SECONDS)
        content = self._do_fetch(url)
        self._pages[url] = content
        return content

    def _do_fetch(self, url: str) -> str:
        """Actual fetch implementation. Uses Scrapling Fetcher; falls back to requests."""
        # Try Scrapling first (better parsing, respects robots.txt)
        try:
            from scrapling import Fetcher
            fetcher = Fetcher()
            page = fetcher.get(url)
            try:
                return page.body.decode("utf-8", errors="replace")
            except Exception:
                return page.text or ""
        except ImportError:
            pass  # Scrapling not installed, fall back to requests
        except Exception as e:
            print(f"  [WARN] Scrapling fetch failed for {url}: {e}")

        # Fallback to requests
        try:
            import requests
            resp = requests.get(url, timeout=30, headers={
                "User-Agent": "Mozilla/5.0 (NZ School Finder crawler; educational project)"
            })
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            print(f"  [WARN] Failed to fetch {url}: {e}")
            return ""

    # ── Pipeline ─────────────────────────────────────

    # All extractable parts — used for --only filtering
    EXTRACT_PARTS = ["subjects", "sports", "arts", "clubs", "fees", "curriculum", "zone", "logo"]

    # Modules required for APPROVED status; others are optional (PARTIAL ok without them)
    # subjects + sports = core data; fees/curriculum/arts/clubs = important but partial ok
    REQUIRED_MODULES = ["subjects", "sports"]

    # Minimum thresholds for required modules to qualify as "present"
    # Below these counts, the module is considered incomplete
    REQUIRED_THRESHOLDS = {"subjects": 10, "sports": 5}

    def crawl(self, only: list[str] | None = None) -> SchoolData:
        """
        Run the crawl pipeline: discover → extract → validate.

        Args:
            only: If provided, only extract these parts (e.g. ["subjects", "fees"]).
                  Must be a subset of EXTRACT_PARTS.
                  None means extract all parts.
        """
        # Determine which parts to extract
        all_parts = [
            ("subjects", self.extract_subjects),
            ("sports", self.extract_sports),
            ("arts", self.extract_arts),
            ("clubs", self.extract_clubs),
            ("fees", self.extract_fees),
            ("curriculum", self.extract_curriculum),
            ("zone", self.extract_zone),
            ("logo", self.extract_logo),
        ]
        if only:
            invalid = set(only) - set(self.EXTRACT_PARTS)
            if invalid:
                raise ValueError(f"Unknown parts: {invalid}. Valid: {self.EXTRACT_PARTS}")
            parts = [(name, method) for name, method in all_parts if name in only]
        else:
            parts = all_parts

        part_label = ", ".join(name for name, _ in parts) if only else "all"
        print(f"\n{'='*60}")
        print(f"  Crawling: {self.school_name} (#{self.school_number})")
        print(f"  Site type: {self.SITE_TYPE}")
        print(f"  Website: {self.website}")
        print(f"  Parts: {part_label}")
        print(f"{'='*60}\n")

        self.data = SchoolData(self.school_number, self.school_name)
        self.data.site_type = self.SITE_TYPE
        self.data.crawled_at = datetime.now().isoformat()

        # Step 1: Discover pages (always runs)
        total = len(parts) + 1
        print(f"[1/{total}] Discovering pages...")
        self.discover_pages()
        print(f"      Found {len(self._pages)} pages")

        # Extract selected parts
        for step, (name, method) in enumerate(parts, start=2):
            print(f"[{step}/{total}] Extracting {name}...")
            try:
                method()
            except Exception as e:
                self.data.warnings.append(f"Failed to extract {name}: {e}")
                print(f"      [WARN] {e}")

        # Finalize pages_crawled (after all extractions, not just discovery)
        self.data.pages_crawled = list(self._pages.keys())

        # Validate
        self._validate()

        # Save log
        self._save_log()

        # Generate review report
        self._generate_review_report()

        print(f"\n{'='*60}")
        print(f"  Crawl complete: {self.school_name}")
        print(f"  Subjects: {len(self.data.subjects)}")
        print(f"  Sports: {len(self.data.sports)}")
        print(f"  Arts: {len(self.data.arts)}")
        print(f"  Clubs: {len(self.data.clubs)}")
        print(f"  Fees: {'Yes' if self.data.intl_tuition_annual else 'No'}")
        print(f"  Logo: {'Yes' if self.data.logo_url else 'No'}")
        print(f"  Zone: {'Yes' if self.data.zone_page_url else 'No'}")
        print(f"  Warnings: {len(self.data.warnings)}")
        print(f"{'='*60}\n")

        return self.data

    # ── Abstract methods (must implement) ────────────

    @abstractmethod
    def discover_pages(self):
        """Find relevant pages on the school website. Populate self._pages."""
        pass

    @abstractmethod
    def extract_subjects(self):
        """Extract subjects → self.data.subjects, self.data.subjects_url"""
        pass

    @abstractmethod
    def extract_sports(self):
        """Extract sports → self.data.sports, self.data.sports_url"""
        pass

    @abstractmethod
    def extract_arts(self):
        """Extract performing arts → self.data.arts, self.data.arts_url"""
        pass

    @abstractmethod
    def extract_clubs(self):
        """Extract clubs/activities → self.data.clubs, self.data.clubs_url"""
        pass

    @abstractmethod
    def extract_fees(self):
        """Extract international fees → self.data.intl_tuition_annual, etc."""
        pass

    @abstractmethod
    def extract_curriculum(self):
        """Extract curriculum systems → self.data.curriculum_systems"""
        pass

    @abstractmethod
    def extract_logo(self):
        """Extract school logo URL → self.data.logo_url"""
        pass

    @abstractmethod
    def extract_zone(self):
        """Extract zone/enrolment info → self.data.zone_*"""
        pass

    # ── Validation ───────────────────────────────────

    def _validate(self):
        """Validate extracted data against crawling-guide rules."""
        # Check subjects against subject_pool
        if self.data.subjects:
            conn = sqlite3.connect(str(DB_PATH))
            cur = conn.cursor()
            cur.execute("SELECT name FROM subject_pool")
            pool_names = {row[0].lower() for row in cur.fetchall()}
            conn.close()

            for subj in self.data.subjects:
                if subj["name"].lower() not in pool_names:
                    self.data.warnings.append(
                        f"Subject '{subj['name']}' not in subject_pool — needs user approval"
                    )

        # Check fees have source URL
        if self.data.intl_tuition_annual and not self.data.intl_fees_url:
            self.data.warnings.append("Fees found but no source URL")

        # Check fees have year — if not, warn and default to current year
        if self.data.intl_tuition_annual and not self.data.intl_fees_year:
            current_year = datetime.now().year
            self.data.intl_fees_year = current_year
            self.data.warnings.append(
                f"Fee year not found on page — defaulting to {current_year}, verify manually"
            )

        # Check curriculum has evidence URLs
        for cs in self.data.curriculum_systems:
            if not cs.get("evidence_url"):
                self.data.warnings.append(
                    f"Curriculum '{cs.get('system')}' has no evidence_url"
                )

    # ── Logging ──────────────────────────────────────

    def _save_log(self):
        """Save crawl log to crawlers/logs/"""
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        log_file = LOG_DIR / f"school_{self.school_number}_{ts}.json"
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(self.data.to_dict(), f, ensure_ascii=False, indent=2)
        print(f"  Log saved: {log_file}")

    # ── Review report ────────────────────────────────

    def _generate_review_report(self):
        """Generate a markdown review report for human review."""
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        report_file = LOG_DIR / f"review_{self.school_number}_{ts}.md"

        d = self.data
        lines = [
            f"# Review Report: {d.school_name} (#{d.school_number})",
            f"",
            f"**Date**: {d.crawled_at}",
            f"**Site type**: {d.site_type}",
            f"**Pages crawled**: {len(d.pages_crawled)}",
            f"",
            f"---",
            f"",
            f"## Checklist",
            f"",
            f"- [ ] Subjects: {len(d.subjects)} items — source from coursebook/course list",
            f"- [ ] Sports: {len(d.sports)} items — count by sport, not by team",
            f"- [ ] Arts: {len(d.arts)} items — performance groups + Kapa Haka only",
            f"- [ ] Clubs: {len(d.clubs)} items — non-Sports/Arts extracurricular",
            f"- [ ] Fees: tuition=${d.intl_tuition_annual} ({d.intl_fees_year or '?'}), homestay=${d.intl_homestay_weekly}/wk",
            f"- [ ] Curriculum: {', '.join(cs.get('system','?') for cs in d.curriculum_systems) or 'none found'}",
            f"- [ ] Logo: {'yes' if d.logo_url else 'no'}",
            f"",
        ]

        if d.warnings:
            lines.append("## Warnings")
            lines.append("")
            for w in d.warnings:
                lines.append(f"- ⚠️ {w}")
            lines.append("")

        lines.append("## Subjects")
        lines.append("")
        if d.subjects:
            lines.append("| # | Name | Raw Name | Source |")
            lines.append("|---|------|----------|--------|")
            for i, s in enumerate(d.subjects, 1):
                lines.append(
                    f"| {i} | {s['name']} | {s.get('raw_name', '')} | {s.get('source_url', '')} |"
                )
        else:
            lines.append("_No subjects extracted._")
        lines.append("")

        lines.append("## Sports")
        lines.append("")
        lines.append(", ".join(d.sports) if d.sports else "_No sports extracted._")
        if d.sports_url:
            lines.append(f"\nSource: {d.sports_url}")
        lines.append("")

        lines.append("## Music / Performing Arts")
        lines.append("")
        lines.append(", ".join(d.arts) if d.arts else "_No arts extracted._")
        if d.arts_url:
            lines.append(f"\nSource: {d.arts_url}")
        lines.append("")

        lines.append("## Clubs")
        lines.append("")
        lines.append(", ".join(d.clubs) if d.clubs else "_No clubs extracted._")
        if d.clubs_url:
            lines.append(f"\nSource: {d.clubs_url}")
        lines.append("")

        lines.append("## International Fees")
        lines.append("")
        if d.intl_tuition_annual:
            year_str = f" ({d.intl_fees_year})" if d.intl_fees_year else " (year unknown)"
            lines.append(f"- Annual tuition: ${d.intl_tuition_annual:,.0f}{year_str}")
            lines.append(f"- Weekly homestay: ${d.intl_homestay_weekly:,.0f}" if d.intl_homestay_weekly else "- Weekly homestay: unknown")
            lines.append(f"- Source: {d.intl_fees_url}")
        else:
            lines.append("_No fees extracted._")
        lines.append("")

        lines.append("## Curriculum Systems")
        lines.append("")
        if d.curriculum_systems:
            for cs in d.curriculum_systems:
                lines.append(f"- **{cs['system']}**: {cs.get('status', '?')} — {cs.get('evidence_url', 'no URL')}")
        else:
            lines.append("_No curriculum info extracted._")
        lines.append("")

        lines.append("## Pages Crawled")
        lines.append("")
        for url in d.pages_crawled:
            lines.append(f"- {url}")
        lines.append("")

        lines.append("---")
        lines.append("")
        # Auto-suggest status based on required module thresholds
        subj_ok = len(d.subjects) >= self.REQUIRED_THRESHOLDS.get("subjects", 10)
        sport_ok = len(d.sports) >= self.REQUIRED_THRESHOLDS.get("sports", 5)
        subj_partial = 0 < len(d.subjects) < self.REQUIRED_THRESHOLDS.get("subjects", 10)
        sport_partial = 0 < len(d.sports) < self.REQUIRED_THRESHOLDS.get("sports", 5)

        if subj_ok and sport_ok:
            suggestion = "APPROVE (subjects >= 10, sports >= 5)"
        elif len(d.subjects) > 0 or len(d.sports) > 0:
            missing = []
            if not subj_ok:
                missing.append(f"subjects: {len(d.subjects)}/{self.REQUIRED_THRESHOLDS['subjects']}")
            if not sport_ok:
                missing.append(f"sports: {len(d.sports)}/{self.REQUIRED_THRESHOLDS['sports']}")
            suggestion = f"PARTIAL ({', '.join(missing)} below threshold)"
        else:
            suggestion = "REJECT (no core data extracted)"
        lines.append(f"## Decision (suggested: {suggestion})")
        lines.append("")
        lines.append("- [ ] **APPROVED** — all required modules meet thresholds + reviewer confirmed")
        lines.append("- [ ] **PARTIAL** — some data available, missing modules noted (use --status partial)")
        lines.append("- [ ] **REJECTED** — data unusable, needs re-crawl or manual fix")
        lines.append("")

        with open(report_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"  Review report: {report_file}")


# ── DB commit helper ─────────────────────────────────

def commit_to_db(data: SchoolData, status: str = CrawlStatus.APPROVED):
    """Write reviewed data to school_web_data and school_subjects tables."""
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    try:
        # school_web_data — INSERT OR REPLACE
        cur.execute(
            """INSERT OR REPLACE INTO school_web_data
            (school_number, subjects, subjects_count, subjects_url,
             sports, sports_count, sports_url,
             music, music_count, music_url,
             activities, activities_count, activities_url,
             intl_fees_url,
             zone_map_url, zone_streets_url, zone_page_url,
             curriculum_systems, logo_url, crawled_at,
             crawl_status, crawl_warnings)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data.school_number,
                json.dumps([s["name"] for s in data.subjects], ensure_ascii=False),
                len(data.subjects),
                data.subjects_url,
                json.dumps(data.sports, ensure_ascii=False),
                len(data.sports),
                data.sports_url,
                json.dumps(data.arts, ensure_ascii=False),
                len(data.arts),
                data.arts_url,
                json.dumps(data.clubs, ensure_ascii=False),
                len(data.clubs),
                data.clubs_url,
                data.intl_fees_url,
                data.zone_map_url,
                data.zone_streets_url,
                data.zone_page_url,
                json.dumps(data.curriculum_systems, ensure_ascii=False),
                data.logo_url,
                data.crawled_at,
                status,
                json.dumps(data.warnings, ensure_ascii=False),
            ),
        )

        # school_subjects — delete + re-insert in transaction
        cur.execute(
            "DELETE FROM school_subjects WHERE school_number = ?",
            (data.school_number,),
        )
        for subj in data.subjects:
            # Look up subject_id from subject_pool
            cur.execute(
                "SELECT id FROM subject_pool WHERE LOWER(name) = LOWER(?)",
                (subj["name"],),
            )
            row = cur.fetchone()
            if row:
                cur.execute(
                    """INSERT INTO school_subjects (school_number, subject_id, raw_name, source_url)
                    VALUES (?, ?, ?, ?)""",
                    (data.school_number, row[0], subj.get("raw_name", ""), subj.get("source_url", "")),
                )

        # school_fees — insert or detect conflict
        if data.intl_tuition_annual and data.intl_fees_year:
            cur.execute(
                "SELECT tuition_annual, homestay_weekly FROM school_fees WHERE school_number = ? AND year = ?",
                (data.school_number, data.intl_fees_year),
            )
            existing = cur.fetchone()
            if existing:
                old_tuition, old_homestay = existing
                tuition_match = old_tuition == data.intl_tuition_annual
                homestay_match = old_homestay == data.intl_homestay_weekly
                if tuition_match and homestay_match:
                    # Same amounts — just update crawled_at
                    cur.execute(
                        "UPDATE school_fees SET crawled_at = ?, fees_url = ? WHERE school_number = ? AND year = ?",
                        (data.crawled_at, data.intl_fees_url, data.school_number, data.intl_fees_year),
                    )
                else:
                    # Conflict — do NOT overwrite, warn for human review
                    conflict_msg = (
                        f"⚠️ FEE CONFLICT for school #{data.school_number} year {data.intl_fees_year}: "
                        f"DB has tuition=${old_tuition}, homestay=${old_homestay} | "
                        f"New crawl has tuition=${data.intl_tuition_annual}, homestay=${data.intl_homestay_weekly}. "
                        f"NOT overwriting — requires human review."
                    )
                    data.warnings.append(conflict_msg)
                    print(f"  {conflict_msg}")
            else:
                # New record — insert
                cur.execute(
                    """INSERT INTO school_fees (school_number, year, tuition_annual,
                       homestay_weekly, fees_url, crawled_at)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (data.school_number, data.intl_fees_year, data.intl_tuition_annual,
                     data.intl_homestay_weekly, data.intl_fees_url, data.crawled_at),
                )

        conn.commit()
        print(f"  ✅ Committed to database: {data.school_name} (#{data.school_number})")
    except Exception as e:
        conn.rollback()
        print(f"  ❌ Failed to commit: {e}")
        raise
    finally:
        conn.close()
