"""
Northcote College (School #32) — Drupal

Website: https://www.northcote.school.nz
Site type: Drupal
Sources:
  - Subjects: /teaching-learning/course-directory
  - Sports: /extra-curricular/sport/sports-offered
  - Arts: /extra-curricular/performing-arts/
  - Clubs: /extra-curricular/ (cultural groups + service)
  - Fees: /international/ (fees not public)
  - Zone: /enrolments/zone-information
"""

import re

from ..templates.standard_html import StandardHtmlCrawler


class NorthcoteCrawler(StandardHtmlCrawler):

    SITE_TYPE = "drupal"
    BASE = "https://www.northcote.school.nz"
    SUBJECTS_URL = "https://www.northcote.school.nz/teaching-learning/course-directory"
    SPORTS_URL = "https://www.northcote.school.nz/extra-curricular/sport/sports-offered"
    ARTS_URL = "https://www.northcote.school.nz/extra-curricular/performing-arts/"
    CLUBS_URL = "https://www.northcote.school.nz/extra-curricular/"
    FEES_URL = "https://www.northcote.school.nz/international/"
    ZONE_URL = "https://www.northcote.school.nz/enrolments/zone-information"

    def discover_pages(self):
        super().discover_pages()
        for url in [self.SUBJECTS_URL, self.SPORTS_URL, self.ARTS_URL,
                    self.CLUBS_URL, self.FEES_URL, self.ZONE_URL]:
            self.fetch_page(url)

    # ── Subjects ──────────────────────────────────────

    SUBJECT_MAPPING = {
        "Te Reo Māori": "Te Reo Maori",
        "Fashion and Textiles": "Textiles",
        "Hard Materials Technology": "Materials and Processing Technology",
        "Carpentry": "Construction",
        "Design and Visual Communication": "Design & Visual Communication",
        "Senior Digital Technology Courses": "Digital Technology",
        "Nutrition": "Food Technology",
        "Hospitality and Professional Cookery": "Hospitality",
        "Visual Art": "Painting",
        "English Language": "ESOL",
        "Sports Studies": "Physical Education",
    }

    SUBJECT_SKIP = {
        "Junior English",         # covered by English
        "Senior English",         # covered by English
        "Junior Mathematics",     # covered by Mathematics
        "Senior Mathematics",     # covered by Mathematics
        "Junior Science",         # covered by Science
        "Senior Science",         # covered by Science
        "Junior Courses",         # vague — social sciences
        "Senior Courses",         # vague — social sciences
        "Junior Technology",      # covered by specific tech subjects
        "Junior Te Reo Māori",    # covered by Te Reo Maori
        "Senior Te Reo Māori",    # covered by Te Reo Maori
        "Learning Support Centre (LSC)",  # support service
        "Mainstream Support Services",    # support service
    }

    def extract_subjects(self):
        """Extract subjects from course directory and department pages."""
        self.data.subjects_url = self.SUBJECTS_URL

        # Compiled from course directory + department pages
        all_subjects = [
            # Core
            "English", "Mathematics", "Science",
            "Physical Education", "Health",
            # Sciences (from senior science)
            "Biology", "Chemistry", "Physics",
            # Social Sciences (from senior courses page)
            "Business Studies", "Classical Studies", "Economics",
            "Geography", "History", "Psychology", "Tourism",
            # Languages
            "French", "Japanese", "Chinese", "Spanish", "Te Reo Māori",
            "English Language",  # ESOL
            # Arts
            "Dance", "Drama", "Music", "Visual Art",
            # Technology
            "Design and Visual Communication",
            "Fashion and Textiles", "Hard Materials Technology",
            "Carpentry", "Senior Digital Technology Courses",
            "Nutrition", "Hospitality and Professional Cookery",
            # Media
            "Media Studies",
            # Sports Studies (PE pathway)
            "Sports Studies",
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
        """Extract sports from sports-offered page."""
        self.data.sports_url = self.SPORTS_URL
        content = self._pages.get(self.SPORTS_URL, "")
        if not content:
            self.data.warnings.append("Could not fetch sports page")
            return

        # From the sports-offered page
        known_sports = [
            "AFL", "Athletics", "Badminton", "Basketball", "Cricket",
            "Cross Country", "Cycling", "Dragon Boating", "Equestrian",
            "Football", "Hockey", "Netball", "Orienteering", "Rugby",
            "Skiing", "Snowboarding", "Softball", "Swimming",
            "Table Tennis", "Tag", "Tennis", "Touch",
            "Underwater Hockey", "Volleyball", "Water Polo",
        ]
        for sport in known_sports:
            if sport.lower() in content.lower():
                self.data.sports.append(sport)

    # ── Arts / Performing Arts ────────────────────────

    def extract_arts(self):
        """Extract performing arts from performing arts page."""
        self.data.arts_url = self.ARTS_URL
        content = self._pages.get(self.ARTS_URL, "")
        if not content:
            self.data.warnings.append("Could not fetch performing arts page")
            return

        # From performing arts page + extra-curricular cultural section
        known_arts = [
            "Kapa Haka", "Jazz Band", "Street Band",
            "Chamber Music", "Tongan Performance Group",
        ]
        for item in known_arts:
            if item.lower() in content.lower():
                self.data.arts.append(item)

        # Also check clubs page for cultural performance groups
        clubs_content = self._pages.get(self.CLUBS_URL, "")
        if clubs_content:
            if "tongan performance" in clubs_content.lower():
                if "Tongan Performance Group" not in self.data.arts:
                    self.data.arts.append("Tongan Performance Group")

        if re.search(r'choir', content, re.IGNORECASE):
            self.data.arts.append("Choir")

    # ── Clubs ─────────────────────────────────────────

    def extract_clubs(self):
        """Extract clubs from extra-curricular page."""
        self.data.clubs_url = self.CLUBS_URL
        content = self._pages.get(self.CLUBS_URL, "")
        if not content:
            return

        # From the extra-curricular page — cultural groups and service
        known_clubs = [
            "Lion Dancers", "K-Pop Dance Crew",
        ]
        for club in known_clubs:
            if club.lower() in content.lower():
                self.data.clubs.append(club)

    # ── Fees ──────────────────────────────────────────

    def extract_fees(self):
        """International fees not publicly listed on website."""
        self.data.intl_fees_url = self.FEES_URL
        # Fees are not displayed on the public website.
        # Students directed to contact the school.
        self.data.intl_fees_year = None
        self.data.intl_tuition_annual = None
        self.data.intl_homestay_weekly = None

    # ── Curriculum ────────────────────────────────────

    def extract_curriculum(self):
        """Northcote College offers NCEA."""
        self.data.curriculum_systems = [
            {
                "system": "NCEA",
                "status": "offered",
                "evidence_url": "https://www.northcote.school.nz/teaching-learning/course-directory",
            },
        ]

    # ── Logo ──────────────────────────────────────────

    def extract_logo(self):
        # /sites/default/files/logo.png — Drupal default logo location.
        # Dimensions not confirmed; use and flag for review.
        self.data.logo_url = "https://www.northcote.school.nz/sites/default/files/logo.png"

    # ── Zone ──────────────────────────────────────────

    def extract_zone(self):
        self.data.zone_page_url = "https://www.northcote.school.nz/enrolments/zone-information"
        self.data.zone_map_url = "https://www.northcote.school.nz/sites/default/files/pdf/NC%20Zone.jpg"
