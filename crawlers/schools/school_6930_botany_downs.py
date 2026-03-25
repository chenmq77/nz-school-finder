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
    SPORTS_URL = "https://www.bdsc.school.nz/co-curricular/sports/"
    ARTS_URL = "https://www.bdsc.school.nz/co-curricular/the-arts/"
    MUSIC_URL = "https://www.bdsc.school.nz/co-curricular/the-arts/music/"
    DANCE_URL = "https://www.bdsc.school.nz/co-curricular/the-arts/dance/"
    DRAMA_URL = "https://www.bdsc.school.nz/co-curricular/the-arts/drama-and-theatre/"
    CLUBS_URL = "https://www.bdsc.school.nz/co-curricular/"
    FEES_URL = "https://www.bdsc.school.nz/international/"
    FEES_PDF_URL = "https://www.bdsc.school.nz/wp-content/uploads/International-Fees-Dates.pdf"
    ZONE_URL = "https://www.bdsc.school.nz/key-information/enrolment/"

    def discover_pages(self):
        super().discover_pages()
        for url in [self.SUBJECTS_URL, self.SPORTS_URL, self.ARTS_URL,
                    self.MUSIC_URL, self.DANCE_URL, self.DRAMA_URL,
                    self.CLUBS_URL, self.FEES_URL, self.ZONE_URL]:
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
        """Extract sports from sports page (Sports Awards list)."""
        self.data.sports_url = self.SPORTS_URL
        content = self._pages.get(self.SPORTS_URL, "")
        if not content:
            self.data.warnings.append("Could not fetch sports page")
            return

        # Sports from Sports Awards and sports page content
        known_sports = [
            "Athletics", "Badminton", "Baseball", "Basketball",
            "Cricket", "Cross Country", "Football",
            "Hockey", "Lacrosse", "Netball", "Orienteering",
            "Rugby", "Rugby League", "Swimming",
            "Table Tennis", "Tennis", "Touch",
            "Volleyball",
        ]
        for sport in known_sports:
            if sport.lower() in content.lower():
                self.data.sports.append(sport)

    # ── Arts / Performing Arts ────────────────────────

    def extract_arts(self):
        """Extract performing arts from 3 sub-pages: music, dance, drama."""
        self.data.arts_url = self.ARTS_URL

        # Music sub-page: Concert Band, Orchestra, Ukulele Group, Rock Bands, Flute Choir, Chamber Groups
        music = self._pages.get(self.MUSIC_URL, "")
        if music:
            music_groups = [
                "Concert Band", "Orchestra", "Ukulele Group",
                "Rock Bands", "Flute Choir", "Chamber Groups",
                "Jazz Band", "Choir",
            ]
            for g in music_groups:
                if g.lower() in music.lower():
                    self.data.arts.append(g)

        # Dance sub-page: Pulse, Stage Challenge, SDNZ Megacrew, Bring it On, Kapa Haka
        dance = self._pages.get(self.DANCE_URL, "")
        if dance:
            dance_groups = [
                "SDNZ Megacrew", "Stage Challenge", "Bring it On",
            ]
            for g in dance_groups:
                if g.lower() in dance.lower():
                    self.data.arts.append(g)
            if re.search(r'kapa\s*haka', dance, re.IGNORECASE):
                self.data.arts.append("Kapa Haka")

        # Drama sub-page: Sheilah Winn Shakespeare, Theatre Sports, School Production
        drama = self._pages.get(self.DRAMA_URL, "")
        if drama:
            drama_groups = [
                "Sheilah Winn Shakespeare", "Theatre Sports",
                "School Production",
            ]
            for g in drama_groups:
                if g.lower() in drama.lower():
                    self.data.arts.append(g)

        # Wearable Art (from main arts page)
        main = self._pages.get(self.ARTS_URL, "")
        if main and re.search(r'wearable\s*art', main, re.IGNORECASE):
            self.data.arts.append("Wearable Art")
        if main and re.search(r'showquest', main, re.IGNORECASE):
            self.data.arts.append("Showquest")

    # ── Clubs ─────────────────────────────────────────

    def extract_clubs(self):
        """Extract clubs from co-curricular page."""
        self.data.clubs_url = self.CLUBS_URL
        content = self._pages.get(self.CLUBS_URL, "")
        if not content:
            return

        known_clubs = [
            "Debating", "Model United Nations", "Chess",
            "Robotics", "Science Club", "Digital Technology Club",
            "Board Game Club", "E-Sports Club",
            "Spoken Word Poetry", "Writing Club",
            "Enviroschools", "Amnesty International",
            "Origami Club", "Crochet Club", "Knitting Club",
            "Juggling Club", "Media Club",
        ]
        for club in known_clubs:
            if club.lower() in content.lower():
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
