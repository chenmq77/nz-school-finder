"""
Mt Albert Grammar School (School #69) — WordPress

Website: https://www.mags.school.nz
Site type: WordPress
Sources:
  - Subjects: /academic/subject-information/
  - Sports: /sport-culture/sport/
  - Arts: /sport-culture/arts-culture/ (music, dance, drama sub-pages)
  - Clubs: /sport-culture/clubs/
  - Fees: /international-fees-2026/ (PDF)
  - Zone: /the-school/enrolment-scheme-zone/
"""

import re

from ..templates.standard_html import StandardHtmlCrawler


class MagsCrawler(StandardHtmlCrawler):

    SITE_TYPE = "wordpress"
    BASE = "https://www.mags.school.nz"
    SUBJECTS_URL = "https://www.mags.school.nz/academic/subject-information/"
    SPORTS_URL = "https://www.mags.school.nz/sport-culture/sport/"
    ARTS_URL = "https://www.mags.school.nz/sport-culture/arts-culture/"
    MUSIC_URL = "https://www.mags.school.nz/co-curricular/music/"
    DANCE_URL = "https://www.mags.school.nz/co-curricular/dance/"
    DRAMA_URL = "https://www.mags.school.nz/co-curricular/drama/"
    CLUBS_URL = "https://www.mags.school.nz/sport-culture/clubs/"
    FEES_URL = "https://www.mags.school.nz/international/how-to-apply/"
    ZONE_URL = "https://www.mags.school.nz/the-school/enrolment-scheme-zone/"

    def discover_pages(self):
        super().discover_pages()
        for url in [self.SUBJECTS_URL, self.SPORTS_URL, self.ARTS_URL,
                    self.MUSIC_URL, self.DANCE_URL, self.DRAMA_URL,
                    self.CLUBS_URL, self.FEES_URL, self.ZONE_URL]:
            self.fetch_page(url)

    # ── Subjects ──────────────────────────────────────

    # MAGS subject navigation lists learning areas; individual subjects extracted
    # from sub-pages and course handbook.
    # Mapping: raw name → subject_pool name
    SUBJECT_MAPPING = {
        "Te Reo Māori": "Te Reo Maori",
        "Visual Art": "Painting",
        "AgriBusiness": "Agricultural and Horticultural Science",
        "Agricultural Science": "Agricultural and Horticultural Science",
        "Food & Hospitality": "Food Technology",
        "Design and Visual Communication": "Design & Visual Communication",
        "Digital Technologies": "Digital Technology",
        "Textiles Technology": "Textiles",
        "Tourism and Travel": "Tourism",
        "Samoan": "Gagana Samoa",
        "Tongan": "Lea Faka-Tonga",
        "Commerce": "Business Studies",
    }

    SUBJECT_SKIP = {
        "MAGnet",                  # school-specific enrichment programme
        "Outdoor Education",       # not in subject pool
    }

    def extract_subjects(self):
        """Extract subjects from subject information sub-pages."""
        self.data.subjects_url = self.SUBJECTS_URL

        # Subjects from navigation + sub-page content:
        # Subject Information sub-pages: AgriBusiness, Classical Studies, Commerce,
        # English, Food & Hospitality, Health, Languages, Mathematics, Media Studies,
        # Performing Arts, Outdoor Education, PE, Science, Social Science, Technology,
        # Visual Art, Te Reo Māori
        all_subjects = [
            # Core
            "English", "Mathematics", "Science", "Physical Education", "Health",
            "Social Studies",
            # Sciences (from Science sub-page)
            "Biology", "Chemistry", "Physics",
            "Agricultural Science", "Horticulture",
            # Social Sciences (from Social Science sub-page)
            "Geography", "History", "Economics",
            "Classical Studies",
            # Commerce (from Commerce sub-page)
            "Accounting", "Business Studies",
            # Languages
            "French", "Japanese", "Samoan", "Tongan",
            "Te Reo Māori", "Chinese", "ESOL",
            # Performing Arts
            "Music", "Dance", "Drama",
            # Visual Arts
            "Visual Art", "Photography", "Design",
            "Design and Visual Communication",
            # Technology
            "Digital Technologies", "Food & Hospitality",
            "Textiles Technology",
            # Media
            "Media Studies",
            # Other
            "Tourism",
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
        """Extract sports from sports page — MAGS offers 40+ sports."""
        self.data.sports_url = self.SPORTS_URL
        content = self._pages.get(self.SPORTS_URL, "")
        if not content:
            self.data.warnings.append("Could not fetch sports page")
            return

        # Sports listed on the page (coached, managed, and facilitated)
        known_sports = [
            "Athletics", "Badminton", "Basketball", "Cricket",
            "Cross Country", "Cycling", "Fencing", "Football",
            "Golf", "Hockey", "Lacrosse", "Lawn Bowls",
            "Mountain Biking", "Netball", "Orienteering",
            "Rowing", "Rugby", "Rugby League",
            "Skiing", "Snowboarding", "Softball", "Squash",
            "Swimming", "Table Tennis", "Tennis", "Touch",
            "Triathlon", "Volleyball", "Waka Ama",
            "Water Polo", "Weightlifting", "Wrestling", "Yachting",
        ]
        for sport in known_sports:
            if sport.lower() in content.lower():
                self.data.sports.append(sport)

    # ── Arts / Performing Arts ────────────────────────

    def extract_arts(self):
        """Extract performing arts groups from music, dance, and drama pages."""
        self.data.arts_url = self.ARTS_URL
        music_content = self._pages.get(self.MUSIC_URL, "")
        dance_content = self._pages.get(self.DANCE_URL, "")
        drama_content = self._pages.get(self.DRAMA_URL, "")
        arts_content = self._pages.get(self.ARTS_URL, "")
        content = " ".join([music_content or "", dance_content or "",
                            drama_content or "", arts_content or ""])

        if not content.strip():
            self.data.warnings.append("Could not fetch arts pages")
            return

        # Music ensembles (from /co-curricular/music/)
        music_groups = [
            "String Orchestra", "Jazz Band", "Concert Band",
            "Chamber Group", "Rock Band",
        ]
        for group in music_groups:
            if group.lower() in content.lower():
                self.data.arts.append(group)

        # Choirs — Boys' Choir and Girls' Choir
        if re.search(r"boys['']?\s*choir", content, re.IGNORECASE):
            self.data.arts.append("Boys' Choir")
        if re.search(r"girls['']?\s*choir", content, re.IGNORECASE):
            self.data.arts.append("Girls' Choir")

        # School Orchestra (distinct from String Orchestra)
        if re.search(r'school\s+orchestra', content, re.IGNORECASE):
            self.data.arts.append("School Orchestra")

        # Dance groups (from /co-curricular/dance/)
        if re.search(r'hip\s*hop', content, re.IGNORECASE):
            self.data.arts.append("Hip Hop Mega Crew")

        # Drama groups (from /co-curricular/drama/)
        drama_groups = ["Theatresports", "Musical Theatre Group"]
        for group in drama_groups:
            if group.lower() in content.lower():
                self.data.arts.append(group)

        # Kapa Haka (from arts-culture page / Te Puna o Wairaka)
        if re.search(r'kapa\s*haka', content, re.IGNORECASE):
            self.data.arts.append("Kapa Haka")

    # ── Clubs ─────────────────────────────────────────

    def extract_clubs(self):
        """Extract clubs from clubs page — MAGS has 50+ active clubs."""
        self.data.clubs_url = self.CLUBS_URL
        content = self._pages.get(self.CLUBS_URL, "")
        if not content:
            return

        known_clubs = [
            "Astronomy Club", "Chess Club", "Debating",
            "Dungeons & Dragons Club", "Informatics Olympiad Club",
            "Programming and Coding", "Robotics", "Science Fair Club",
            "Creative Writing", "Zine Club",
            "Model United Nations",
            "Indian Club", "Muslim Club", "Sri Lankan Club",
            "Environment", "Horticultural Club", "TeenAg",
            "Mooting Club",
        ]
        for club in known_clubs:
            if club.lower() in content.lower():
                self.data.clubs.append(club)

        # Rainbow/Pride club
        if re.search(r'rainbow|pride\s*club', content, re.IGNORECASE):
            self.data.clubs.append("MAGS Rainbow Pride Club")

    # ── Fees ──────────────────────────────────────────

    def extract_fees(self):
        """Extract international fees — hardcoded from 2026 PDF.
        Source: /international-fees-2026/ (linked from /international/how-to-apply/)
        PDF title: "International Student Fees 2026" """
        self.data.intl_fees_url = self.FEES_URL
        # From PDF: Full Year Tuition $20,000; Homestay $420/week
        self.data.intl_fees_year = 2026
        self.data.intl_tuition_annual = 20000.0
        self.data.intl_homestay_weekly = 420.0

    # ── Curriculum ────────────────────────────────────

    def extract_curriculum(self):
        """MAGS offers NCEA."""
        self.data.curriculum_systems = [
            {
                "system": "NCEA",
                "status": "offered",
                "evidence_url": self.SUBJECTS_URL,
            },
        ]

    # ── Logo ──────────────────────────────────────────

    def extract_logo(self):
        # The banner logo (558x140) is too wide. Use the schema.org logo which
        # includes the square crest. The 1080x900 white-on-transparent version
        # is not available for MAGS, so we use the banner logo and note it.
        # Best available: the logo PNG has a square crest on the left portion.
        # TODO: find a cropped square crest if one becomes available.
        self.data.logo_url = "https://www.mags.school.nz/wp-content/uploads/2016/12/magslogo-140.png"

    # ── Zone ──────────────────────────────────────────

    def extract_zone(self):
        self.data.zone_page_url = self.ZONE_URL
        self.data.zone_streets_url = "https://www.mags.school.nz/in-zone-streets-2024-2/"
