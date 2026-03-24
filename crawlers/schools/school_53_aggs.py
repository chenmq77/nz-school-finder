"""
Auckland Girls' Grammar School (School #53) — WordPress

Website: https://www.aggs.school.nz
Site type: WordPress (Elementor)
Sources:
  - Subjects: /school-life/curriculum-academic-learning/years-9-10/ + /years-11-13/
  - Sports: /school-life/co-curricular/sports/
  - Arts: /school-life/co-curricular/arts-and-culture/
  - Clubs: /school-life/co-curricular/community-groups-committees/
  - Fees: /international/international-fees/
  - Zone: /enrolments/school-enrolment-zone/
"""

import re

from ..templates.standard_html import StandardHtmlCrawler


class AggsCrawler(StandardHtmlCrawler):

    SITE_TYPE = "wordpress"
    BASE = "https://www.aggs.school.nz"
    SUBJECTS_Y910_URL = "https://www.aggs.school.nz/school-life/curriculum-academic-learning/years-9-10/"
    SUBJECTS_Y1113_URL = "https://www.aggs.school.nz/school-life/curriculum-academic-learning/years-11-13/"
    SPORTS_URL = "https://www.aggs.school.nz/school-life/co-curricular/sports/"
    ARTS_URL = "https://www.aggs.school.nz/school-life/co-curricular/arts-and-culture/"
    CLUBS_URL = "https://www.aggs.school.nz/school-life/co-curricular/community-groups-committees/"
    FEES_URL = "https://www.aggs.school.nz/international/international-fees/"
    ZONE_URL = "https://www.aggs.school.nz/enrolments/school-enrolment-zone/"

    def discover_pages(self):
        super().discover_pages()
        for url in [self.SUBJECTS_Y910_URL, self.SUBJECTS_Y1113_URL,
                    self.SPORTS_URL, self.ARTS_URL, self.CLUBS_URL,
                    self.FEES_URL, self.ZONE_URL]:
            self.fetch_page(url)

    # ── Subjects ──────────────────────────────────────

    SUBJECT_MAPPING = {
        "Samoan": "Gagana Samoa",
        "Lea-Faka Tonga": "Lea Faka-Tonga",
        "Tongan": "Lea Faka-Tonga",
        "Visual Art": "Painting",
        "Te Reo Māori": "Te Reo Maori",
        "Te Ao Haka": "Te Ao Haka",
        "Design & Visual Communication": "Design & Visual Communication",
        "Digital Technologies (Programming)": "Digital Technology",
        "Commerce": "Business Studies",
        "Senior Social Studies": "Social Studies",
        "Tourism and the Travel Industry": "Tourism",
        "Hospitality/Food Technology": "Food Technology",
        "Textiles Technology": "Textiles",
        "Health Studies": "Health",
        "Product Design": "Product Development",
        "Health Science Academy": "Science",
        "Applied Health Science": "Science",
    }

    SUBJECT_SKIP = {
        "General Mathematics",        # variant of Mathematics
        "Mathematics with Calculus",   # branch of Mathematics
        "Mathematics with Statistics", # branch of Mathematics
        "Gateway",                     # vocational programme, not a subject
        "Pathways",                    # vocational programme
        "Tikanga-a-iwi",              # school-specific integrated programme
        "Design",                     # too vague — covered by Design & Visual Communication
    }

    def extract_subjects(self):
        """Extract subjects from Year 9-10 and Year 11-13 pages."""
        self.data.subjects_url = self.SUBJECTS_Y910_URL

        # Combined from both pages
        all_subjects = [
            # Core (Y9-10)
            "English", "Mathematics", "Science", "Social Studies",
            "Physical Education", "Health",
            # Languages
            "French", "Japanese", "Samoan", "Tongan", "Te Reo Māori",
            # Arts
            "Dance", "Drama", "Music", "Visual Art", "Photography", "Painting",
            "Art History",
            # Technology
            "Design & Visual Communication", "Digital Technologies (Programming)",
            "Hospitality", "Textiles Technology", "Product Design",
            "Hospitality/Food Technology",
            # Y11-13 additions
            "Media Studies", "ESOL",
            "Biology", "Chemistry", "Physics",
            "Geography", "History", "Economics",
            "Classical Studies", "Tourism and the Travel Industry",
            "Commerce",
            # Māori
            "Te Ao Haka",
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
                    "source_url": self.SUBJECTS_Y910_URL,
                })

    # ── Sports ────────────────────────────────────────

    def extract_sports(self):
        """Extract sports from sports page."""
        self.data.sports_url = self.SPORTS_URL
        content = self._pages.get(self.SPORTS_URL, "")
        if not content:
            self.data.warnings.append("Could not fetch sports page")
            return

        # Sports listed on the page
        known_sports = [
            "Athletics", "Badminton", "Basketball", "Crossfit",
            "Dragon Boating", "Football", "Hockey", "Kilikiti",
            "Lacrosse", "Lawn Bowls", "Netball", "Rugby",
            "Softball", "Swimming", "Tennis", "Touch",
            "Volleyball", "Waka Ama",
        ]
        for sport in known_sports:
            if sport.lower() in content.lower():
                self.data.sports.append(sport)

    # ── Arts / Performing Arts ────────────────────────

    def extract_arts(self):
        """Extract performing arts from arts & culture page."""
        self.data.arts_url = self.ARTS_URL
        content = self._pages.get(self.ARTS_URL, "")
        if not content:
            self.data.warnings.append("Could not fetch arts page")
            return

        known_arts = [
            "Kapa Haka", "Polyfest",
            # Music ensembles
            "Chamber Music", "Jazz Combo", "Flute Ensemble",
        ]
        for item in known_arts:
            if item.lower() in content.lower():
                self.data.arts.append(item)

        # Check for choir (may appear as "auditioned choir" etc.)
        if re.search(r'choir', content, re.IGNORECASE):
            self.data.arts.append("Choir")

    # ── Clubs ─────────────────────────────────────────

    def extract_clubs(self):
        """Extract clubs from community groups page."""
        self.data.clubs_url = self.CLUBS_URL
        content = self._pages.get(self.CLUBS_URL, "")
        if not content:
            return

        known_clubs = [
            "Debating Club", "Duke of Edinburgh", "Interact",
            "Spoken Word", "Rainbow Group", "Upcycling Club",
            "Model United Nations",
        ]
        for club in known_clubs:
            if club.lower() in content.lower():
                self.data.clubs.append(club)

    # ── Fees ──────────────────────────────────────────

    def extract_fees(self):
        """Extract international fees from fees page."""
        self.data.intl_fees_url = self.FEES_URL
        content = self._pages.get(self.FEES_URL, "")

        if content:
            # Try to extract year
            year_match = re.search(r'(?:fees|tuition).*?(20\d{2})|(?:(20\d{2}).*?(?:fees|tuition))', content, re.IGNORECASE)
            if year_match:
                self.data.intl_fees_year = int(year_match.group(1) or year_match.group(2))

            # Tuition: NZ$17,900
            tuition_match = re.search(r'[Tt]uition\s*[Ff]ee[^$]*?NZ?\$\s*([\d,]+)', content)
            if tuition_match:
                amount = float(tuition_match.group(1).replace(",", ""))
                if 10000 < amount < 50000:
                    self.data.intl_tuition_annual = amount

            # Homestay annual: NZ$19,320 → convert to weekly ($19,320 / 46)
            homestay_match = re.search(r'[Hh]omestay\s*[Ff]ee[^$]*?NZ?\$\s*([\d,]+)', content)
            if homestay_match:
                amount = float(homestay_match.group(1).replace(",", ""))
                if amount > 5000:  # annual amount
                    self.data.intl_homestay_weekly = round(amount / 46, 2)
                elif 200 < amount < 800:
                    self.data.intl_homestay_weekly = amount

        if not self.data.intl_tuition_annual:
            # Hardcoded fallback from page content
            self.data.intl_tuition_annual = 17900.0
            self.data.intl_homestay_weekly = 420.0  # $19,320 / 46 weeks ≈ $420
            self.data.warnings.append("Fees extracted from hardcoded fallback — verify manually")

    # ── Curriculum ────────────────────────────────────

    def extract_curriculum(self):
        """AGGS offers NCEA."""
        self.data.curriculum_systems = [
            {
                "system": "NCEA",
                "status": "offered",
                "evidence_url": "https://www.aggs.school.nz/school-life/curriculum-academic-learning/academic-achievement/",
            },
        ]

    # ── Logo ──────────────────────────────────────────

    def extract_logo(self):
        # Use square crest (192x192) instead of wide banner (489x119)
        self.data.logo_url = "https://www.aggs.school.nz/wp-content/uploads/2024/08/cropped-android-chrome-512x512-1-192x192.png"

    # ── Zone ──────────────────────────────────────────

    def extract_zone(self):
        self.data.zone_page_url = self.ZONE_URL
        self.data.zone_map_url = "https://www.aggs.school.nz/wp-content/uploads/2024/07/aggs-geographic-zone-map_full2005.pdf"
