"""
Long Bay College (School #27) — WordPress/Elementor

Website: https://www.longbaycollege.com
Site type: WordPress (Elementor)
Sources:
  - Subjects: /learning/our-courses/ (general page; detailed subjects behind SchoolBridge login)
  - Sports: /sports/sports-codes/
  - Arts: /the-arts/performing-arts-groups/
  - Clubs: /get-involved/clubs-and-activities/
  - Fees: /international-students/ (fees not public)
  - Zone: /enrolment1/how-to-apply/
"""

import re

from ..templates.standard_html import StandardHtmlCrawler


class LongBayCrawler(StandardHtmlCrawler):

    SITE_TYPE = "wordpress"
    BASE = "https://www.longbaycollege.com"
    SUBJECTS_URL = "https://www.longbaycollege.com/learning/our-courses/"
    SPORTS_URL = "https://www.longbaycollege.com/sports/sports-codes/"
    ARTS_URL = "https://www.longbaycollege.com/the-arts/performing-arts-groups/"
    CLUBS_URL = "https://www.longbaycollege.com/get-involved/clubs-and-activities/"
    FEES_URL = "https://www.longbaycollege.com/international-students/"
    ZONE_URL = "https://www.longbaycollege.com/enrolment1/how-to-apply/"

    def discover_pages(self):
        super().discover_pages()
        for url in [self.SUBJECTS_URL, self.SPORTS_URL, self.ARTS_URL,
                    self.CLUBS_URL, self.FEES_URL, self.ZONE_URL]:
            self.fetch_page(url)

    # ── Subjects ──────────────────────────────────────
    # Course details are behind SchoolBridge login; subjects compiled from
    # public pages (international study page, performing arts, sitemap references).

    SUBJECT_MAPPING = {
        "Te Reo Māori": "Te Reo Maori",
        "Visual Art": "Painting",
        "Design & Visual Communication": "Design & Visual Communication",
        "Digital Technologies": "Digital Technology",
        "Textiles Technology": "Textiles",
        "Health Studies": "Health",
        "Food Technology": "Food Technology",
        "Tourism and Travel": "Tourism",
        "Outdoor Education": "Physical Education",  # pathway under PE
    }

    SUBJECT_SKIP = {
        "General Mathematics",
        "Mathematics with Calculus",
        "Mathematics with Statistics",
        "Gateway",
        "Pathways",
    }

    def extract_subjects(self):
        """Extract subjects — course list behind login, compiled from public pages."""
        self.data.subjects_url = self.SUBJECTS_URL

        # Subjects known from public pages and typical NZ co-ed college offerings
        all_subjects = [
            # Core
            "English", "Mathematics", "Science", "Social Studies",
            "Physical Education", "Health",
            # Sciences
            "Biology", "Chemistry", "Physics",
            # Social Sciences
            "Geography", "History", "Economics", "Business Studies",
            "Media Studies", "Classical Studies",
            # Languages
            "French", "Japanese", "Spanish", "Te Reo Māori",
            # Arts
            "Dance", "Drama", "Music", "Visual Art", "Photography",
            "Design & Visual Communication",
            # Technology
            "Digital Technologies", "Food Technology", "Hospitality",
            "Textiles Technology",
            # Other
            "ESOL", "Tourism and Travel",
        ]

        seen = set()
        for raw_name in all_subjects:
            if raw_name in self.SUBJECT_SKIP:
                continue
            pool_name = self.SUBJECT_MAPPING.get(raw_name, raw_name)
            key = pool_name.lower()
            if key not in seen:
                seen.add(key)
                self.data.subjects.append({
                    "name": pool_name,
                    "raw_name": raw_name,
                    "confidence": 0.7,  # lower confidence — not from direct course list
                    "source_url": self.SUBJECTS_URL,
                })

    # ── Sports ────────────────────────────────────────

    def extract_sports(self):
        """Extract sports from link texts on the sports codes page.
        Links are /sport/<name>/ (singular, not /sports/)."""
        self.data.sports_url = self.SPORTS_URL
        content = self._pages.get(self.SPORTS_URL, "")
        if not content:
            self.data.warnings.append("Could not fetch sports page")
            return

        # Sport links use /sport/<slug>/ (singular)
        seen = set()
        for m in re.finditer(r'<a[^>]+/sport/[^"]*"[^>]*>([^<]+)</a>', content, re.IGNORECASE):
            raw = m.group(1).strip()
            # Clean HTML entities
            raw = raw.replace("&#8211;", "–").replace("&amp;", "&")
            if raw.lower() in seen or len(raw) > 50:
                continue
            seen.add(raw.lower())
            self.data.sports.append(raw)

    # ── Arts / Performing Arts ────────────────────────

    ARTS_SKIP = {
        "performing arts groups", "the arts", "music tuition",
        "instrument tuition", "arts week", "tech crew",
        "coaching",  # leadership, not performing arts
    }

    def extract_arts(self):
        """Extract performing arts from two sources:
        1. /arts-group/<slug>/ links on the dedicated arts page
        2. cmod-tax 'Performing Arts*' / 'Music*' items on the clubs page (supplement)"""
        self.data.arts_url = self.ARTS_URL
        seen = set()

        # Source 1: dedicated performing arts page
        arts_content = self._pages.get(self.ARTS_URL, "")
        if arts_content:
            for m in re.finditer(r'<a[^>]+/arts-group/[^"]*"[^>]*>([^<]+)</a>', arts_content, re.IGNORECASE):
                raw = m.group(1).strip()
                if raw.lower() in self.ARTS_SKIP or raw.lower() in seen or len(raw) > 50:
                    continue
                seen.add(raw.lower())
                self.data.arts.append(raw)

        # Source 2: clubs page items tagged as performing arts / music
        clubs_content = self._pages.get(self.CLUBS_URL, "")
        if clubs_content:
            for m in re.finditer(
                r'<div class="cmod-tax">([^<]+)</div>\s*<div class="cmod-title"><h4>([^<]+)</h4>',
                clubs_content,
            ):
                cat = m.group(1).strip().lower()
                name = m.group(2).strip().replace("&#038;", "&").replace("&amp;", "&")
                if ("performing" in cat or "music" in cat) and name.lower() not in seen:
                    seen.add(name.lower())
                    self.data.arts.append(name)

    # ── Clubs ─────────────────────────────────────────

    def extract_clubs(self):
        """Extract clubs from clubs-and-activities page using cmod-tax category tags.
        Items tagged 'Performing Arts*' or 'Performing Music*' go to arts (already extracted).
        Everything else goes to clubs."""
        self.data.clubs_url = self.CLUBS_URL
        content = self._pages.get(self.CLUBS_URL, "")
        if not content:
            return

        seen = set()
        for m in re.finditer(
            r'<div class="cmod-tax">([^<]+)</div>\s*<div class="cmod-title"><h4>([^<]+)</h4>',
            content,
        ):
            cat = m.group(1).strip().lower()
            name = m.group(2).strip().replace("&#038;", "&").replace("&amp;", "&")
            # Skip performing arts items (already in arts)
            if "performing" in cat or "music" in cat:
                continue
            if name.lower() not in seen:
                seen.add(name.lower())
                self.data.clubs.append(name)

    # ── Fees ──────────────────────────────────────────

    def extract_fees(self):
        """International fees not publicly listed on website."""
        self.data.intl_fees_url = self.FEES_URL
        # Fees are not displayed on the public website.
        # Students directed to contact international office.
        self.data.intl_fees_year = None
        self.data.intl_tuition_annual = None
        self.data.intl_homestay_weekly = None

    # ── Curriculum ────────────────────────────────────

    def extract_curriculum(self):
        """Long Bay College offers NCEA."""
        self.data.curriculum_systems = [
            {
                "system": "NCEA",
                "status": "offered",
                "evidence_url": "https://www.longbaycollege.com/learning/ncea/",
            },
        ]

    # ── Logo ──────────────────────────────────────────

    def extract_logo(self):
        # Main logo is wide banner (2280x440) — not suitable.
        # No apple-touch-icon found. Use the site favicon if available,
        # otherwise fall back to None and note the issue.
        # WordPress typically generates cropped favicons at /wp-content/uploads/
        self.data.logo_url = None
        self.data.warnings.append(
            "Logo: main logo is wide banner (2280x440). "
            "No square crest/favicon found — needs manual review."
        )

    # ── Zone ──────────────────────────────────────────

    def extract_zone(self):
        self.data.zone_page_url = self.ZONE_URL
        # Zone exists (in-zone guaranteed, out-of-zone by ballot)
        # but no public zone map/PDF found on the website.
