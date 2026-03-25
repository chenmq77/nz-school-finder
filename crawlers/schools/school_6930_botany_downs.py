"""
Botany Downs Secondary College (School #6930) — WordPress

Website: https://www.bdsc.school.nz
Site type: WordPress
Sources:
  - Subjects: /curriculum/subject-information/ (option book PDFs)
  - Sports: /co-curricular/sports/
  - Arts: /co-curricular/the-arts/
  - Clubs: /co-curricular/
  - Fees: /wp-content/uploads/International-Fees-Dates.pdf
  - Zone: /key-information/enrolment/
"""

import re

from ..templates.standard_html import StandardHtmlCrawler


class BotanyDownsCrawler(StandardHtmlCrawler):

    SITE_TYPE = "wordpress"
    BASE = "https://www.bdsc.school.nz"
    SUBJECTS_URL = "https://www.bdsc.school.nz/curriculum/subject-information/"
    SPORTS_URL = "https://www.bdsc.school.nz/co-curricular/sport/"
    ARTS_URL = "https://www.bdsc.school.nz/co-curricular/the-arts/"
    MUSIC_URL = "https://www.bdsc.school.nz/co-curricular/the-arts/music/"
    DANCE_URL = "https://www.bdsc.school.nz/co-curricular/the-arts/dance/"
    DRAMA_URL = "https://www.bdsc.school.nz/co-curricular/the-arts/drama-and-theatre/"
    CLUBS_URL = "https://www.bdsc.school.nz/co-curricular/"
    CULTURAL_URL = "https://www.bdsc.school.nz/co-curricular/cultural-groups/"
    FEES_URL = "https://www.bdsc.school.nz/international/"
    FEES_PDF_URL = "https://www.bdsc.school.nz/wp-content/uploads/International-Fees-Dates.pdf"
    ZONE_URL = "https://www.bdsc.school.nz/key-information/enrolment/"

    def discover_pages(self):
        super().discover_pages()
        for url in [self.SUBJECTS_URL, self.SPORTS_URL, self.ARTS_URL,
                    self.CLUBS_URL, self.CULTURAL_URL,
                    self.FEES_URL, self.ZONE_URL]:
            self.fetch_page(url)

    # ── Subjects ──────────────────────────────────────

    # Subjects compiled from option books (Year 10, Level 1-3 PDFs on subjects page).
    # Learning areas: English & EAL, Health & PE, Languages, Mathematics & Statistics,
    # Science, Social Sciences, Technology, Visual & Performing Arts.
    SUBJECT_MAPPING = {
        "Visual Art": "Painting",
        "Te Reo Māori": "Te Reo Maori",
        "Design and Visual Communication": "Design & Visual Communication",
        "Digital Technologies": "Digital Technology",
        "Food & Hospitality": "Food Technology",
        "Hospitality": "Hospitality",
        "Commerce": "Business Studies",
        "Textiles Technology": "Textiles",
        "Health Studies": "Health",
        "Tourism and Travel": "Tourism",
    }

    SUBJECT_SKIP = {
        "Active Well Being",       # school-specific programme, not a standalone subject
        "Gateway",                 # vocational programme
        "Pathways",                # vocational programme
        "MAGnet",                  # school-specific programme
    }

    def extract_subjects(self):
        """Extract subjects from option book content (Level 1-3 + Year 10)."""
        self.data.subjects_url = self.SUBJECTS_URL

        # Subjects from option books and learning area pages:
        # Core + Sciences + Social Sciences + Languages + Arts + Technology
        all_subjects = [
            # Core (compulsory at Level 1)
            "English", "Mathematics", "Science", "Physical Education", "Health",
            # Sciences
            "Biology", "Chemistry", "Physics",
            # Social Sciences
            "Geography", "History", "Economics", "Business Studies",
            "Classical Studies", "Tourism",
            # Languages
            "French", "Japanese", "Chinese", "Te Reo Māori", "ESOL",
            # Arts — Visual
            "Visual Art", "Photography", "Design",
            "Design and Visual Communication",
            # Arts — Performing
            "Music", "Dance", "Drama", "Media Studies",
            # Technology
            "Digital Technologies", "Food & Hospitality", "Hospitality",
            "Textiles Technology",
            # Other
            "Accounting", "Social Studies",
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
                    "confidence": 0.9,
                    "source_url": self.SUBJECTS_URL,
                })

    # ── Sports ────────────────────────────────────────

    def extract_sports(self):
        """Extract sports from the sport page.
        Page uses vc_toggle accordion — each sport is an <h5 class="vc_custom_heading">."""
        self.data.sports_url = self.SPORTS_URL
        content = self._pages.get(self.SPORTS_URL, "")
        if not content:
            self.data.warnings.append("Could not fetch sport page")
            return

        # Extract from vc_toggle headings: <h5 ... class="vc_custom_heading">Sport Name</h5>
        seen = set()
        for m in re.finditer(r'vc_custom_heading[^>]*>\s*([^<]+?)\s*</h', content):
            name = m.group(1).strip()
            if name.lower() not in seen and len(name) < 50:
                seen.add(name.lower())
                self.data.sports.append(name)

    # ── Arts / Performing Arts ────────────────────────

    def extract_arts(self):
        """Extract performing arts from the main arts page.
        Page has 4 columns (DANCE, DRAMA, MUSIC, WEARABLE ART) under "WHAT'S ON OFFER".
        Each column: <h5>CATEGORY</h5> then <p>item1<br>item2<br>...</p>."""
        self.data.arts_url = self.ARTS_URL
        content = self._pages.get(self.ARTS_URL, "")
        if not content:
            self.data.warnings.append("Could not fetch arts page")
            return

        # Find the "WHAT'S ON OFFER" section — 4 columns with h5 + p items
        # Structure: <h5>DANCE</h5><p>item<br/>item</p> ... <h5>DRAMA</h5><p>...</p>
        # Extract all <p> content after each <h5> in the vc_col-sm-3 columns
        seen = set()
        for m in re.finditer(
            r'<h5>(DANCE|DRAMA|MUSIC|WEARABLE ART)</h5>\s*<p>(.*?)</p>',
            content, re.DOTALL
        ):
            category = m.group(1)
            items_html = m.group(2)
            # Split by <br> tags
            items = re.split(r'<br\s*/?>|\n', items_html)
            for item in items:
                name = re.sub(r'<[^>]+>', '', item).strip()
                name = name.replace('&#8211;', '–').replace('&amp;', '&')
                if name and name.lower() not in seen and len(name) < 60:
                    seen.add(name.lower())
                    self.data.arts.append(name)

    # ── Clubs ─────────────────────────────────────────

    def extract_clubs(self):
        """Extract clubs from co-curricular page + cultural groups page.
        Cultural groups page uses <ul><li> list structure."""
        self.data.clubs_url = self.CULTURAL_URL

        # Source 1: Cultural groups page — <ul><li> list
        cultural = self._pages.get(self.CULTURAL_URL, "")
        seen = set()
        if cultural:
            for m in re.finditer(r'<li>([^<]+)</li>', cultural):
                name = m.group(1).strip()
                name = name.replace('&#8220;', '"').replace('&#8221;', '"')
                if name and name.lower() not in seen and len(name) < 60:
                    seen.add(name.lower())
                    self.data.clubs.append(name)

        # Source 2: General co-curricular page for non-sport/non-arts clubs
        content = self._pages.get(self.CLUBS_URL, "")
        if content:
            extra_clubs = [
                "Debating", "Model United Nations", "Chess",
                "Robotics", "E-Sports", "Enviroschools",
            ]
            for club in extra_clubs:
                if club.lower() in content.lower() and club.lower() not in seen:
                    seen.add(club.lower())
                    self.data.clubs.append(club)

    # ── Fees ──────────────────────────────────────────

    def extract_fees(self):
        """Extract international fees — hardcoded from 2026 PDF.
        Source: /wp-content/uploads/International-Fees-Dates.pdf
        PDF shows 2026 term dates, fees are current for 2026."""
        self.data.intl_fees_url = self.FEES_PDF_URL
        # From PDF: Full Year Tuition $21,000; Homestay $400/week
        self.data.intl_fees_year = 2026
        self.data.intl_tuition_annual = 21000.0
        self.data.intl_homestay_weekly = 400.0

    # ── Curriculum ────────────────────────────────────

    def extract_curriculum(self):
        """BDSC offers NCEA."""
        self.data.curriculum_systems = [
            {
                "system": "NCEA",
                "status": "offered",
                "evidence_url": self.SUBJECTS_URL,
            },
        ]

    # ── Logo ──────────────────────────────────────────

    def extract_logo(self):
        # Nearly-square logo (1080x900) from schema.org markup
        self.data.logo_url = "https://www.bdsc.school.nz/wp-content/uploads/2017/06/BotanyDownsSecondaryCollege_LogoWhite_1080x900.png"

    # ── Zone ──────────────────────────────────────────

    def extract_zone(self):
        self.data.zone_page_url = self.ZONE_URL
        self.data.zone_streets_url = "https://www.bdsc.school.nz/enrolments-3-2/in-zone-street-addresses/"
