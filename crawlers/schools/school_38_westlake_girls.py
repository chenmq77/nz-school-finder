"""
Westlake Girls' High School (School #38) — WordPress

Website: https://www.westlakegirls.school.nz
Site type: WordPress
Sources:
  - Subjects: /student-life/academic/curriculum-learning/ (limited; full list via SchoolPoint)
  - Sports: /student-life/sports/
  - Arts: /student-life/music/ + /student-life/drama-and-dance/
  - Clubs: /student-life/clubs-activities/ (PDF only, limited)
  - Fees: international.westlakegirls.school.nz/fees/ (PDF)
  - Zone: /enrolment/school-zone/
"""

import re

from ..templates.standard_html import StandardHtmlCrawler


class WestlakeGirlsCrawler(StandardHtmlCrawler):

    SITE_TYPE = "wordpress"
    BASE = "https://www.westlakegirls.school.nz"
    CURRICULUM_URL = "https://www.westlakegirls.school.nz/student-life/academic/curriculum-learning/"
    SPORTS_URL = "https://www.westlakegirls.school.nz/student-life/sports/"
    MUSIC_URL = "https://www.westlakegirls.school.nz/student-life/music/"
    DRAMA_URL = "https://www.westlakegirls.school.nz/student-life/drama-and-dance/"
    CLUBS_URL = "https://www.westlakegirls.school.nz/student-life/clubs-activities/"
    INTL_URL = "https://international.westlakegirls.school.nz/fees/"
    ZONE_URL = "https://www.westlakegirls.school.nz/enrolment/school-zone/"

    def discover_pages(self):
        super().discover_pages()
        for url in [self.CURRICULUM_URL, self.SPORTS_URL, self.MUSIC_URL,
                    self.DRAMA_URL, self.CLUBS_URL, self.ZONE_URL]:
            self.fetch_page(url)

    # ── Subjects ──────────────────────────────────────

    # WGHS curriculum page doesn't list individual subjects (uses SchoolPoint).
    # Subject list compiled from curriculum page mentions + NCEA standard offerings.
    SUBJECT_MAPPING = {
        "Te Reo Māori": "Te Reo Maori",
        "Samoan": "Gagana Samoa",
        "Tongan": "Lea Faka-Tonga",
        "Korean": "Korean",
        "Visual Art": "Painting",
        "Design and Visual Communication": "Design & Visual Communication",
        "Textiles Technology": "Textiles",
        "Product Design": "Product Development",
    }

    def extract_subjects(self):
        """Extract subjects — compiled from curriculum page + standard NCEA offerings."""
        self.data.subjects_url = self.CURRICULUM_URL

        # WGHS is a high-decile school offering comprehensive NCEA subjects
        all_subjects = [
            # Core
            "English", "Mathematics", "Science", "Social Studies",
            "Physical Education", "Health",
            # Sciences
            "Biology", "Chemistry", "Physics", "Earth and Space Science",
            # Social Sciences
            "Geography", "History", "Economics", "Business Studies",
            "Classical Studies", "Media Studies",
            # Languages
            "French", "Spanish", "Japanese", "Chinese",
            "Te Reo Māori", "Samoan", "Tongan", "Korean",
            # Arts
            "Music", "Drama", "Dance", "Visual Art", "Photography",
            "Art History", "Painting",
            # Technology
            "Design and Visual Communication", "Digital Technology",
            "Food Technology", "Textiles Technology", "Product Design",
            "Hospitality",
            # Other
            "ESOL", "Tourism",
        ]

        seen = set()
        for raw_name in all_subjects:
            pool_name = self.SUBJECT_MAPPING.get(raw_name, raw_name)
            key = pool_name.lower()
            if key not in seen:
                seen.add(key)
                self.data.subjects.append({
                    "name": pool_name,
                    "raw_name": raw_name,
                    "confidence": 0.7,  # lower confidence — inferred, not scraped from page
                    "source_url": self.CURRICULUM_URL,
                })

    # ── Sports ────────────────────────────────────────

    def extract_sports(self):
        """Extract sports from sports page."""
        self.data.sports_url = self.SPORTS_URL
        content = self._pages.get(self.SPORTS_URL, "")
        if not content:
            self.data.warnings.append("Could not fetch sports page")
            return

        known_sports = [
            "Adventure Racing", "Athletics", "Badminton", "Basketball",
            "Beach Volleyball", "Cheerleading", "Cricket", "Cycling",
            "Distance Running", "Diving", "Equestrian", "Football",
            "Golf", "Gymsports", "Hockey", "Kilikiti",
            "Lacrosse", "Motocross", "Multisport",
            "Netball", "Orienteering", "Rock Climbing", "Rowing",
            "Rugby", "Sailing", "Snowsports", "Softball", "Squash",
            "Swimming", "Table Tennis", "Tag", "Tennis", "Touch",
            "Volleyball", "Waka Ama", "Waterpolo",
        ]
        for sport in known_sports:
            if sport.lower() in content.lower():
                self.data.sports.append(sport)

    # ── Arts / Performing Arts ────────────────────────

    def extract_arts(self):
        """Extract performing arts from music + drama pages."""
        self.data.arts_url = self.MUSIC_URL
        music_content = self._pages.get(self.MUSIC_URL, "")
        drama_content = self._pages.get(self.DRAMA_URL, "")

        # Music ensembles from music page
        # key = search term on page, value = display name (with type for clarity)
        music_groups = {
            # Choirs — original names are Italian/Māori, add "Choir" suffix for clarity
            "Cantare": "Cantare Choir",
            "Choralation": "Choralation Choir",
            "Cigno Voce": "Cigno Voce Choir",
            "Nota Bella": "Nota Bella Choir",
            "Kotahi Voices": "Kotahi Voices Choir",
            # Orchestras & Bands
            "Westlake Symphony Orchestra": "Westlake Symphony Orchestra",
            "Westlake Chamber Orchestra": "Westlake Chamber Orchestra",
            "Westlake Concert Band": "Westlake Concert Band",
            "Westlake Big Band": "Westlake Big Band",
            "Taharoto Strings": "Taharoto Strings",
            "Symphonic Band": "Symphonic Band",
            "Jazz Band": "Jazz Band",
            "Chamber Music": "Chamber Music",
            "Rock Bands": "Rock Bands",
            "Silver Keys Flute Choir": "Silver Keys Flute Choir",
        }
        if music_content:
            for search_term, display_name in music_groups.items():
                if search_term.lower() in music_content.lower():
                    self.data.arts.append(display_name)

        # Drama/dance from drama page
        drama_groups = [
            "Theatresports", "Sheilah Winn Shakespeare",
            "Dance Club", "Dance Troupes", "Bollywood Dance Group",
            "Showquest", "K-Pop Cover Group",
        ]
        if drama_content:
            for group in drama_groups:
                if group.lower() in drama_content.lower():
                    self.data.arts.append(group)

        # Kapa Haka — check both pages
        combined = (music_content or "") + " " + (drama_content or "")
        if re.search(r'kapa\s*haka', combined, re.IGNORECASE):
            self.data.arts.append("Kapa Haka")

    # ── Clubs ─────────────────────────────────────────

    def extract_clubs(self):
        """Extract clubs from PDF "Clubs and Extra-Curricular Activities 2025"."""
        self.data.clubs_url = self.CLUBS_URL

        # Clubs extracted from PDF (73 pages, one club per page)
        # Excludes items already in arts (choirs, orchestras, bands, dance) and sports
        self.data.clubs = [
            "Amnesty International",
            "Anime / Manga Club",
            "Arabic Language Club",
            "Art Drawing Club",
            "Art Media Exploration",
            "Aviation Project",
            "Biology Olympiad",
            "Brain Bee",
            "Bridge Club",
            "Buddy Reading",
            "Chemistry Olympiad",
            "Chinese Club",
            "Cultural Communication Club",
            "Debating",
            "Diversity Club",
            "Enviro Club",
            "Esports & Code Club",
            "Filipino Club",
            "French Club",
            "Gardening Club",
            "Korean Club",
            "Inspire Christian Club",
            "International Homework Club",
            "Journalism Club",
            "Kaitiaki Club",
            "Knitting / Crocheting Club",
            "Letters to Strangers",
            "Model United Nations Assembly",
            "Neurodiversity Club",
            "Pasifika Student Committee",
            "Philosophy Club",
            "Rotary Interact Club",
            "Spanish Club",
            "Tech Innovation Club",
            "Volunteering Club",
            "Wearable Art Club",
            "Westlake Medical Research",
            "Parallax Writing Club",
            "World Vision 40 Hour Challenge",
            "Young Physicist's Tournament",
        ]

    # ── Fees ──────────────────────────────────────────

    def extract_fees(self):
        """Extract fees from PDF data (2026/2027 schedule)."""
        # From PDF: "WGHS International Schedule of fees 2026/2027"
        # 2026: Tuition $23,000, Homestay $18,000/yr (45wks × $400/wk)
        # 2027: Tuition $25,000, Homestay $20,250/yr (45wks × $450/wk)
        self.data.intl_fees_url = self.INTL_URL

        # Store 2026 fees (current year)
        self.data.intl_fees_year = 2026
        self.data.intl_tuition_annual = 23000.0
        self.data.intl_homestay_weekly = 400.0

    # ── Curriculum ────────────────────────────────────

    def extract_curriculum(self):
        """WGHS offers NCEA."""
        self.data.curriculum_systems = [
            {
                "system": "NCEA",
                "status": "offered",
                "evidence_url": "https://www.westlakegirls.school.nz/student-life/academic/ncea/",
            },
        ]

    # ── Logo ──────────────────────────────────────────

    def extract_logo(self):
        # Use square crest (242x242) instead of wide banner SVG (2800x574)
        self.data.logo_url = "https://www.westlakegirls.school.nz/wp-content/uploads/2024/09/WGHS-Shield-crest-only-RGB.png"

    # ── Zone ──────────────────────────────────────────

    def extract_zone(self):
        self.data.zone_page_url = self.ZONE_URL
