"""
Kelston Girls' College (School #84) — Standard HTML (Sporty.co.nz platform)

Website: https://www.kelstongirls.school.nz
Site type: Standard HTML (Sporty CMS)
Sources:
  - Subjects: /learning-at-kgc/our-curriculum + /enrolment/international-students (more detail)
  - Sports: /opportunities-at-kgc/sports
  - Arts: /opportunities-at-kgc/arts-and-cultural
  - Fees: PDF via Sporty asset ID 425d043c-aff7-4a54-ad54-450b46fd8fcc
  - Zone: /enrolment/how-to-enrol
"""

import re

from ..templates.standard_html import StandardHtmlCrawler


class KelstonGirlsCrawler(StandardHtmlCrawler):

    BASE = "https://www.kelstongirls.school.nz"
    CURRICULUM_URL = "https://www.kelstongirls.school.nz/learning-at-kgc/our-curriculum"
    SPORTS_URL = "https://www.kelstongirls.school.nz/opportunities-at-kgc/sports"
    ARTS_URL = "https://www.kelstongirls.school.nz/opportunities-at-kgc/arts-and-cultural"
    INTL_URL = "https://www.kelstongirls.school.nz/enrolment/international-students"
    FEES_PDF_URL = "https://www.sporty.co.nz/asset/downloadasset?id=425d043c-aff7-4a54-ad54-450b46fd8fcc"
    ENROL_URL = "https://www.kelstongirls.school.nz/enrolment/how-to-enrol"

    def discover_pages(self):
        """Fetch homepage and known source pages."""
        super().discover_pages()
        for url in [self.CURRICULUM_URL, self.SPORTS_URL, self.ARTS_URL, self.INTL_URL, self.ENROL_URL]:
            self.fetch_page(url)

    # ── Subjects ──────────────────────────────────────

    # KGC uses an integrated curriculum model (Rōpū) at junior level.
    # Subject list compiled from curriculum page + known NCEA subject offerings.
    # Mapping: raw name → subject_pool name
    SUBJECT_MAPPING = {
        "Samoan": "Gagana Samoa",
        "Tongan": "Lea Faka-Tonga",
        "Visual Art": "Painting",
        "Soft Materials": "Textiles",
        "Commerce": "Business Studies",
        "Te Reo Maori": "Te Reo Maori",
        "Design and Visual Communication": "Design & Visual Communication",
        "Agriculture": "Agricultural and Horticultural Science",
        "Earth & Space": "Earth and Space Science",
    }

    SUBJECT_SKIP = {
        "Science Literacy",        # junior integrated module, not a standalone subject
        "Numeracy",                # junior integrated module
        "English Language Learning",  # same as ESOL
        "Mōhio",                   # self-directed learning framework, not a subject
        "Project-Based Learning",  # pedagogical approach
    }

    def extract_subjects(self):
        """Extract subjects from curriculum page + international students page."""
        self.data.subjects_url = self.CURRICULUM_URL

        # Subjects from /learning-at-kgc/our-curriculum + /enrolment/international-students
        all_subjects = [
            # Core
            "English", "Mathematics", "Science", "Social Studies",
            "Physical Education", "Health",
            # Sciences (from international page: "Biology, Chemistry, Physics, Agriculture, Earth & Space")
            "Biology", "Chemistry", "Physics",
            "Agriculture", "Earth & Space",
            # Social Sciences (from international page: "Geography, History, Business")
            "Geography", "History",
            # Languages
            "Te Reo Maori", "Samoan", "Tongan", "ESOL",
            # Arts
            "Music", "Visual Art", "Drama", "Dance",
            # Technology
            "Food Technology", "Soft Materials", "Digital Technology",
            "Design and Visual Communication",
            # Commerce
            "Commerce",
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
                    "confidence": 0.8,
                    "source_url": self.CURRICULUM_URL,
                })

    # ── Sports ────────────────────────────────────────

    def extract_sports(self):
        """Extract sports from sports page + international students page."""
        self.data.sports_url = self.SPORTS_URL
        # Combine content from both pages for broader matching
        sports_content = self._pages.get(self.SPORTS_URL, "")
        intl_content = self._pages.get(self.INTL_URL, "")
        content = (sports_content or "") + " " + (intl_content or "")

        if not sports_content:
            self.data.warnings.append("Could not fetch sports page")

        # Sports from sports page + international page
        # (intl page lists: "Rugby Union, Basketball, Football, Netball, Volleyball and Badminton")
        known_sports = [
            "Netball", "Basketball", "Rugby", "Weightlifting", "Badminton",
            "Athletics", "Cross Country", "Swimming", "Touch",
            "Football", "Volleyball", "Table Tennis", "Ki O Rahi",
            "Cricket", "Softball", "Hockey", "Tennis",
        ]
        for sport in known_sports:
            if sport.lower() in content.lower():
                self.data.sports.append(sport)

    # ── Arts / Performing Arts ────────────────────────

    def extract_arts(self):
        """Extract performing arts groups from arts & cultural page."""
        self.data.arts_url = self.ARTS_URL
        content = self._pages.get(self.ARTS_URL, "")
        if not content:
            self.data.warnings.append("Could not fetch arts page")
            return

        known_arts = [
            "Choir", "Kapa Haka", "Spoken Word Poetry",
            "Polyfest",
        ]
        for item in known_arts:
            if item.lower() in content.lower():
                self.data.arts.append(item)

    # ── Clubs ─────────────────────────────────────────

    def extract_clubs(self):
        """Extract cultural groups as clubs from arts & cultural page."""
        self.data.clubs_url = self.ARTS_URL
        content = self._pages.get(self.ARTS_URL, "")
        if not content:
            return

        # 8 cultural groups mentioned on the page
        cultural_groups = [
            "Samoan", "Tongan", "Cook Island", "Niuean",
            "Tokelauan", "Indian", "Filipino",
        ]
        for group in cultural_groups:
            if group.lower() in content.lower():
                self.data.clubs.append(f"{group} Cultural Group")

        # Māori cultural group (check separately as "Māori" appears in many contexts)
        if re.search(r'(?:māori|maori)\s+(?:group|cultural)', content, re.IGNORECASE):
            self.data.clubs.append("Māori Cultural Group")

    # ── Fees ──────────────────────────────────────────

    def extract_fees(self):
        """Extract international fees — hardcoded from 2026 PDF."""
        # From PDF: "Kelston Girls College International Student Fees 2026"
        # Tuition Fee: $16,800 per year
        # Homestay Fee for 7 nights: $420 per student (per week)
        self.data.intl_fees_url = self.INTL_URL
        self.data.intl_fees_year = 2026
        self.data.intl_tuition_annual = 16800.0
        self.data.intl_homestay_weekly = 420.0

    # ── Curriculum ────────────────────────────────────

    def extract_curriculum(self):
        """KGC offers NCEA."""
        self.data.curriculum_systems = [
            {
                "system": "NCEA",
                "status": "offered",
                "evidence_url": self.CURRICULUM_URL,
            },
        ]

    # ── Logo ──────────────────────────────────────────

    def extract_logo(self):
        """KGC logo from Sporty CDN."""
        self.data.logo_url = "https://prodcdn.sporty.co.nz/cms/12088/logo.jpg"

    # ── Zone ──────────────────────────────────────────

    def extract_zone(self):
        """KGC has an enrolment zone — info on enrolment page."""
        self.data.zone_page_url = self.ENROL_URL
