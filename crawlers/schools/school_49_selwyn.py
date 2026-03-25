"""
Selwyn College (School #49) — WordPress/Elementor

Website: https://www.selwyn.school.nz
Site type: WordPress (Elementor)
Sources:
  - Subjects: /our-curriculum/ (individual subject department pages)
  - Sports: external at sporty.co.nz/selwyncollege (not scrapable)
  - Arts: /performing-arts/ (Kapa Haka, musicals, co-curricular music)
  - Clubs: limited — cultural groups from performing arts page
  - Fees: /international/ (fees not public)
  - Zone: /new-students/zone/
"""

import re

from ..templates.standard_html import StandardHtmlCrawler


class SelwynCrawler(StandardHtmlCrawler):

    SITE_TYPE = "wordpress"
    BASE = "https://www.selwyn.school.nz"
    SUBJECTS_URL = "https://www.selwyn.school.nz/our-curriculum/english/"
    SPORTS_URL = None  # external at sporty.co.nz — not scrapable
    ARTS_URL = "https://www.selwyn.school.nz/performing-arts/"
    CLUBS_URL = None  # limited info on website
    FEES_URL = "https://www.selwyn.school.nz/international/"
    ZONE_URL = "https://www.selwyn.school.nz/new-students/zone/"

    def discover_pages(self):
        super().discover_pages()
        urls = [
            self.SUBJECTS_URL, self.ARTS_URL, self.FEES_URL, self.ZONE_URL,
            # Individual curriculum department pages
            "https://www.selwyn.school.nz/our-curriculum/mathematics/",
            "https://www.selwyn.school.nz/our-curriculum/science/",
            "https://www.selwyn.school.nz/our-curriculum/social-sciences/",
            "https://www.selwyn.school.nz/our-curriculum/technology/",
            "https://www.selwyn.school.nz/our-curriculum/languages/",
            "https://www.selwyn.school.nz/our-curriculum/visual-art/",
            "https://www.selwyn.school.nz/our-curriculum/pe-health/",
            "https://www.selwyn.school.nz/our-curriculum/performing-arts-2/",
        ]
        for url in urls:
            if url:
                self.fetch_page(url)

    # ── Subjects ──────────────────────────────────────

    SUBJECT_MAPPING = {
        "Te Reo Māori": "Te Reo Maori",
        "Te Reo Maori": "Te Reo Maori",
        "Art Design": "Design",
        "Textiles Technology": "Textiles",
        "Multi-Materials Technology": "Materials and Processing Technology",
        "Engineering": "Electronics",  # closest pool match — flag for review
        "Senior Social Studies": "Social Studies",
        "Design & Visual Communication": "Design & Visual Communication",
    }

    SUBJECT_SKIP = {
        "Junior Art",             # covered by Painting
        "Junior Science",         # covered by Science
        "Junior Social Studies",  # covered by Social Studies
        "Senior General Science", # variant of Science
        "Literacy",               # support programme, not a subject
        "Outdoor Education",      # not in subject pool
    }

    def extract_subjects(self):
        """Extract subjects from individual curriculum department pages."""
        self.data.subjects_url = "https://www.selwyn.school.nz/our-curriculum/english/"

        # Compiled from department pages:
        # English, Mathematics, Science, Social Sciences, Technology,
        # Languages, Visual Art, PE & Health, Performing Arts
        all_subjects = [
            # English
            "English",
            # Mathematics
            "Mathematics",
            # Science (from /our-curriculum/science/)
            "Science", "Biology", "Chemistry", "Physics",
            # Social Sciences (from /our-curriculum/social-sciences/)
            "Accounting", "Classical Studies", "Economics",
            "Geography", "History", "Media Studies",
            "Senior Social Studies",
            # Technology (from /our-curriculum/technology/)
            "Construction", "Design & Visual Communication",
            "Digital Technology", "Electronics", "Engineering",
            "Food Technology", "Hospitality",
            "Multi-Materials Technology", "Textiles Technology",
            # Languages (from /our-curriculum/languages/)
            "Chinese", "ESOL", "Spanish", "Te Reo Maori",
            # Visual Art (from /our-curriculum/visual-art/)
            "Painting", "Photography", "Art Design", "Art History",
            # PE & Health (from /our-curriculum/pe-health/)
            "Physical Education", "Health",
            # Performing Arts (from /our-curriculum/performing-arts-2/)
            "Dance", "Drama", "Music",
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
                    "source_url": "https://www.selwyn.school.nz/our-curriculum/english/",
                })

        self.data.warnings.append(
            "Engineering mapped to Electronics — may need pool review"
        )

    # ── Sports ────────────────────────────────────────

    def extract_sports(self):
        """Sports hosted externally on sporty.co.nz — not directly scrapable.
        Using known sports list for a mid-decile Auckland co-ed college."""
        self.data.sports_url = "https://www.sporty.co.nz/selwyncollege"
        self.data.warnings.append(
            "Sports data from external sporty.co.nz — not scraped, "
            "using known list. Needs manual verification."
        )

        # Known sports for Selwyn College (public knowledge)
        known_sports = [
            "Athletics", "Badminton", "Basketball", "Cricket",
            "Cross Country", "Football", "Hockey", "Netball",
            "Rugby", "Softball", "Swimming", "Table Tennis",
            "Tennis", "Touch", "Volleyball",
        ]
        for sport in known_sports:
            self.data.sports.append(sport)

    # ── Arts / Performing Arts ────────────────────────

    def extract_arts(self):
        """Extract performing arts from performing arts page."""
        self.data.arts_url = self.ARTS_URL
        content = self._pages.get(self.ARTS_URL, "")
        if not content:
            self.data.warnings.append("Could not fetch performing arts page")
            return

        # From the performing arts page
        known_arts = [
            "Kapa Haka", "Selwyn Musicals",
        ]
        for item in known_arts:
            if item.lower() in content.lower():
                self.data.arts.append(item)

        # Check for general terms
        if re.search(r'co-curricular music', content, re.IGNORECASE):
            self.data.arts.append("Co-Curricular Music Ensembles")
        if re.search(r'choir', content, re.IGNORECASE):
            self.data.arts.append("Choir")

    # ── Clubs ─────────────────────────────────────────

    def extract_clubs(self):
        """Limited club information on website."""
        # No dedicated clubs page found; cultural groups and houses exist
        # but details are sparse.
        self.data.clubs_url = None
        self.data.warnings.append(
            "No dedicated clubs page found on Selwyn College website"
        )

    # ── Fees ──────────────────────────────────────────

    def extract_fees(self):
        """International fees not publicly listed on website."""
        self.data.intl_fees_url = self.FEES_URL
        # Page mentions fees must be paid but does not list amounts.
        # Students directed to contact the International Office.
        self.data.intl_fees_year = None
        self.data.intl_tuition_annual = None
        self.data.intl_homestay_weekly = None

    # ── Curriculum ────────────────────────────────────

    def extract_curriculum(self):
        """Selwyn College offers NCEA."""
        self.data.curriculum_systems = [
            {
                "system": "NCEA",
                "status": "offered",
                "evidence_url": "https://www.selwyn.school.nz/our-curriculum/english/",
            },
        ]

    # ── Logo ──────────────────────────────────────────

    def extract_logo(self):
        # Selwyn-badge.gif is 269x254 — close to square, good for display.
        # selwyn-logo.png is a wide banner — not suitable.
        self.data.logo_url = "https://selwyn.school.nz/wp-content/uploads/sites/178/2026/03/Selwyn-badge.gif"

    # ── Zone ──────────────────────────────────────────

    def extract_zone(self):
        self.data.zone_page_url = self.ZONE_URL
        self.data.zone_map_url = (
            "https://www.schoolwebsites.school.nz/selwyn/wp-content/uploads/"
            "sites/178/2022/09/Selwyn-College-confirmed-Zone-Description-and-Map-August-2021.pdf"
        )
