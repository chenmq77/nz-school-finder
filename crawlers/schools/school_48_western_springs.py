"""
Western Springs College (School #48) — WordPress

Website: https://www.westernsprings.school.nz
Site type: WordPress
Sources:
  - Subjects: /year-9-course-selection/ through /year-13-ncea-level-3-course-book/
  - Sports: /western-springs-college-sport/
  - Arts: /arts/
  - Clubs: /extra-curricular/
  - Fees: /international-enrolment/ (2026 fees PDF)
  - Zone: /enrolment/
"""

import re

from ..templates.standard_html import StandardHtmlCrawler


class WesternSpringsCrawler(StandardHtmlCrawler):

    SITE_TYPE = "wordpress"
    BASE = "https://www.westernsprings.school.nz"
    SUBJECTS_Y9_URL = "https://www.westernsprings.school.nz/year-9-course-selection/"
    SUBJECTS_Y10_URL = "https://www.westernsprings.school.nz/year-10-course-selection/"
    SUBJECTS_Y11_URL = "https://www.westernsprings.school.nz/year-11-course-book/"
    SUBJECTS_Y12_URL = "https://www.westernsprings.school.nz/year-12-ncea-level-2-course-book/"
    SUBJECTS_Y13_URL = "https://www.westernsprings.school.nz/year-13-ncea-level-3-course-book/"
    SPORTS_URL = "https://www.westernsprings.school.nz/western-springs-college-sport/"
    ARTS_URL = "https://www.westernsprings.school.nz/arts/"
    CLUBS_URL = "https://www.westernsprings.school.nz/extra-curricular/"
    FEES_URL = "https://www.westernsprings.school.nz/international-enrolment/"
    ZONE_URL = "https://www.westernsprings.school.nz/enrolment/"

    def discover_pages(self):
        super().discover_pages()
        for url in [self.SUBJECTS_Y9_URL, self.SUBJECTS_Y11_URL,
                    self.SUBJECTS_Y12_URL, self.SUBJECTS_Y13_URL,
                    self.SPORTS_URL, self.ARTS_URL, self.CLUBS_URL,
                    self.FEES_URL, self.ZONE_URL]:
            self.fetch_page(url)

    # ── Subjects ──────────────────────────────────────

    # Subjects compiled from course selection pages (Year 9-13).
    # Year 9: core + language options + arts options
    # Year 11-13: full NCEA subject options from course books
    SUBJECT_MAPPING = {
        "Te Reo Māori": "Te Reo Maori",
        "Visual Art": "Painting",
        "Art Painting": "Painting",
        "Art Photography": "Photography",
        "Art Design": "Design",
        "Visual Arts": "Painting",
        "Design and Visual Communication": "Design & Visual Communication",
        "Digital Technologies": "Digital Technology",
        "Food & Hospitality": "Food Technology",
        "Textiles Technology": "Textiles",
        "English Language": "ESOL",
    }

    SUBJECT_SKIP = {
        "Gateway",                 # vocational programme
        "Māori Studies",           # junior integrated module (Year 9), not a standalone NCEA subject
        "English for Academic Purposes",  # variant of ESOL
    }

    def extract_subjects(self):
        """Extract subjects from Year 9-13 course selection pages."""
        self.data.subjects_url = self.SUBJECTS_Y11_URL

        # Combined from Year 9 course selection + Year 11-13 course books
        all_subjects = [
            # Core
            "English", "Mathematics", "Science", "Social Studies",
            "Physical Education", "Health",
            # Sciences
            "Biology", "Chemistry", "Physics",
            # Social Sciences
            "Geography", "History", "Economics",
            "Classical Studies",
            # Commerce
            "Business Studies", "Accounting",
            # Languages (Year 9: Chinese, French, Te Reo Māori)
            "Chinese", "French", "Te Reo Māori", "ESOL",
            # Performing Arts
            "Music", "Dance", "Drama", "Media Studies",
            # Visual Arts (Year 12-13: Art Design, Art Painting, Art Photography, Art History)
            "Art Painting", "Art Photography", "Art Design", "Art History",
            # Technology
            "Design and Visual Communication", "Digital Technologies",
            "Food & Hospitality", "Textiles Technology",
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
                    "source_url": self.SUBJECTS_Y11_URL,
                })

    # ── Sports ────────────────────────────────────────

    def extract_sports(self):
        """Extract sports from sports page — WSC offers 30+ sports."""
        self.data.sports_url = self.SPORTS_URL
        content = self._pages.get(self.SPORTS_URL, "")
        if not content:
            self.data.warnings.append("Could not fetch sports page")
            return

        # Summer + Winter sports from sports page
        known_sports = [
            "Athletics", "Badminton", "Basketball", "Cricket",
            "Cross Country", "Cycling", "Dragon Boating",
            "Football", "Hockey", "Ki O Rahi", "Lacrosse",
            "Lawn Bowls", "Mountain Biking", "Netball",
            "Orienteering", "Rugby", "Rugby League",
            "Skiing", "Snowboarding", "Softball", "Squash",
            "Swimming", "Tennis", "Touch", "Triathlon",
            "Volleyball", "Waka Ama", "Water Polo", "Yachting",
        ]
        for sport in known_sports:
            if sport.lower() in content.lower():
                self.data.sports.append(sport)

    # ── Arts / Performing Arts ────────────────────────

    def extract_arts(self):
        """Extract performing arts from /arts/ page.
        Page has 3 columns with <h2> headings: Dance, Music, Drama Productions.
        Music items: <b>item<br/></b> inside one <p> block after <h2>Music</h2>
        Drama items: <strong>item</strong> in separate <p> tags after <h2>Drama Productions</h2>
        Dance items: <b>item</b> after <h2>Dance</h2>"""
        self.data.arts_url = self.ARTS_URL
        content = self._pages.get(self.ARTS_URL, "")
        if not content:
            self.data.warnings.append("Could not fetch arts page")
            return

        seen = set()

        # Skip non-group items
        skip = {"instrumentalvocal lessons", "instrumental/vocal lessons",
                "sound and lighting", "senior dance showcases"}

        # Music column: <h2>Music</h2> followed by <p><b>item<br/></b><b>item<br/></b>...</p>
        music_match = re.search(r'<h2>Music</h2>\s*<p>(.*?)</p>', content, re.DOTALL)
        if music_match:
            for m in re.finditer(r'<b>([^<]+?)(?:<br\s*/?>|</b>)', music_match.group(1)):
                name = m.group(1).strip()
                if name and name.lower() not in seen and name.lower() not in skip and len(name) < 50:
                    seen.add(name.lower())
                    self.data.arts.append(name)

        # Dance column: <h2>Dance Productions</h2> then <p><strong>Name</strong></p>
        dance_match = re.search(r'<h2>Dance Productions</h2>(.*?)</div>', content, re.DOTALL)
        if dance_match:
            for m in re.finditer(r'<strong>([^<]+?)</strong>', dance_match.group(1)):
                name = m.group(1).strip().replace("&#8211;", "–")
                if name and name.lower() not in seen and len(name) < 50:
                    seen.add(name.lower())
                    self.data.arts.append(name)

        # Drama column: <h2>Drama Productions</h2> then multiple <p><strong>Name</strong>...</p>
        drama_match = re.search(r'<h2>Drama Productions</h2>(.*?)</div>', content, re.DOTALL)
        if drama_match:
            for m in re.finditer(r'<strong>([^<]+?)</strong>', drama_match.group(1)):
                name = m.group(1).strip()
                if name and name.lower() not in seen and len(name) < 50:
                    seen.add(name.lower())
                    self.data.arts.append(name)

        # Kapa Haka
        if re.search(r'kapa\s*haka', content, re.IGNORECASE) and "kapa haka" not in seen:
            self.data.arts.append("Kapa Haka")

    # ── Clubs ─────────────────────────────────────────

    def extract_clubs(self):
        """Extract clubs from extra-curricular page."""
        self.data.clubs_url = self.CLUBS_URL
        # The /extra-curricular/ page returned 404 during crawl.
        # Clubs may be listed elsewhere or page may be seasonal.
        content = self._pages.get(self.CLUBS_URL, "")
        if not content:
            self.data.warnings.append("Could not fetch clubs page (/extra-curricular/ returned 404)")
            return

        known_clubs = [
            "Debating", "Chess", "Robotics",
            "Environment Club", "Rainbow Group",
            "Duke of Edinburgh",
        ]
        for club in known_clubs:
            if club.lower() in content.lower():
                self.data.clubs.append(club)

    # ── Fees ──────────────────────────────────────────

    def extract_fees(self):
        """Extract international fees — hardcoded from 2026 fees page.
        Source: /international-enrolment/ — "2026 Fees and General Information" PDF.
        Tuition: $20,000/year. Homestay: $400/week standard, $420/week for under-14
        or special dietary. Using standard $400/week rate."""
        self.data.intl_fees_url = self.FEES_URL
        self.data.intl_fees_year = 2026
        self.data.intl_tuition_annual = 20000.0
        self.data.intl_homestay_weekly = 400.0

    # ── Curriculum ────────────────────────────────────

    def extract_curriculum(self):
        """WSC offers NCEA."""
        self.data.curriculum_systems = [
            {
                "system": "NCEA",
                "status": "offered",
                "evidence_url": self.SUBJECTS_Y11_URL,
            },
        ]

    # ── Logo ──────────────────────────────────────────

    def extract_logo(self):
        # og:image has the full school logo; apple-touch-icon is a small cropped version.
        self.data.logo_url = "https://westernsprings.school.nz/wp-content/uploads/2017/07/logos_05.png"

    # ── Zone ──────────────────────────────────────────

    def extract_zone(self):
        self.data.zone_page_url = self.ZONE_URL
        # Zone map is embedded on the enrolment page as an image.
        # Zone checker: Education Counts tool at educationcounts.govt.nz/find-school
