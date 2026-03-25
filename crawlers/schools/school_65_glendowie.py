"""
Glendowie College (School #65) — SchoolBridge / Inbox Design

Website: https://www.gdc.school.nz
Site type: SchoolBridge (Inbox Design platform)
Sources:
  - Subjects: /explore-glendowie-college/academic/ + /international (intl page has full subject list)
  - Sports: /explore-glendowie-college/sport
  - Arts: /explore-glendowie-college/arts-culture
  - Clubs: /explore-glendowie-college/community/clubs-groups
  - Fees: /international (fees not publicly listed — contact school)
  - Zone: /enrolment/school-zone
"""

import re

from ..templates.standard_html import StandardHtmlCrawler


class GlendowieCrawler(StandardHtmlCrawler):

    SITE_TYPE = "schoolbridge"
    BASE = "https://www.gdc.school.nz"
    ACADEMIC_URL = "https://www.gdc.school.nz/explore-glendowie-college/academic/curriculum-pathways"
    INTL_URL = "https://www.gdc.school.nz/international"
    SPORTS_URL = "https://www.gdc.school.nz/explore-glendowie-college/sport"
    ARTS_URL = "https://www.gdc.school.nz/explore-glendowie-college/arts-culture"
    CLUBS_URL = "https://www.gdc.school.nz/explore-glendowie-college/community/clubs-groups"
    ZONE_URL = "https://www.gdc.school.nz/enrolment/school-zone"

    def discover_pages(self):
        super().discover_pages()
        for url in [self.ACADEMIC_URL, self.INTL_URL, self.SPORTS_URL,
                    self.ARTS_URL, self.CLUBS_URL, self.ZONE_URL]:
            self.fetch_page(url)

    # ── Subjects ──────────────────────────────────────

    # Mapping: raw name from website → pool name
    SUBJECT_MAPPING = {
        "Design & Visual Communication (Graphics)": "Design & Visual Communication",
        "Computer courses": "Digital Technology",
        "Outdoor Education": "Physical Education",  # not a standalone pool subject
        "Mandarin": "Chinese",
        "Art": "Painting",  # Visual Arts group — GDC says "Art", map to fine art subject
        "Technology": "Product Development",  # generic "Technology" → most likely practical tech
    }

    # Subjects to SKIP — not standalone subjects in the pool
    SUBJECT_SKIP = {
        "English as a Second Language (ESOL)",  # duplicates ESOL below
        "Technology",      # too generic — GDC has specific tech subjects
        "Outdoor Education",  # not a standard NZQA subject in pool
    }

    def extract_subjects(self):
        """Extract subjects from international page (most complete list) + academic pages."""
        self.data.subjects_url = self.INTL_URL

        # From international page: full subject list quoted directly
        # "English as a Second Language (ESOL), English, Spanish, Mandarin,
        #  Accounting, Mathematics, Science, Biology, Chemistry, Physics,
        #  Geography, History, Economics, Business Studies, Classical Studies,
        #  Electronics, Design & Visual Communication (Graphics), Technology,
        #  Computer courses, Art, Music, Drama, Dance, Physical Education,
        #  Health, Outdoor Education, Hospitality and Food Technology"
        all_subjects = [
            # Core
            "English", "Mathematics", "Science",
            "Physical Education", "Health",
            # Sciences
            "Biology", "Chemistry", "Physics",
            # Social Sciences
            "Geography", "History", "Economics", "Business Studies",
            "Classical Studies",
            # Languages
            "Spanish", "Mandarin", "ESOL",
            # Arts
            "Art", "Music", "Drama", "Dance",
            # Technology
            "Design & Visual Communication (Graphics)", "Electronics",
            "Computer courses", "Food Technology", "Hospitality",
            # Commerce
            "Accounting",
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
                    "source_url": self.INTL_URL,
                })

    # ── Sports ────────────────────────────────────────

    def extract_sports(self):
        """Extract sports from sport page — 29 sports offered."""
        self.data.sports_url = self.SPORTS_URL
        content = self._pages.get(self.SPORTS_URL, "")
        if not content:
            self.data.warnings.append("Could not fetch sports page")
            return

        # From website: Summer + Winter sports (29 total)
        known_sports = [
            # Summer
            "Athletics", "Climbing", "Cricket", "Lawn Bowls",
            "Orienteering", "Rowing", "Surfing", "Swimming",
            "Table Tennis", "Touch Rugby", "Volleyball", "Water Polo", "Yachting",
            # Winter
            "Badminton", "Basketball", "Cycling", "Distance Running",
            "Football", "Hockey", "Lacrosse", "Mountain Biking",
            "Netball", "Rugby Union", "Snow Sports", "Underwater Hockey",
        ]
        for sport in known_sports:
            if sport.lower() in content.lower():
                self.data.sports.append(sport)

        # Also check for Triathlon / Multisport (listed as "Multi-sports: Triathlon")
        if re.search(r'triathlon|multi.?sport', content, re.IGNORECASE):
            self.data.sports.append("Triathlon")

    # ── Arts / Performing Arts ────────────────────────

    def extract_arts(self):
        """Extract performing arts from arts & culture page."""
        self.data.arts_url = self.ARTS_URL
        content = self._pages.get(self.ARTS_URL, "")

        # Also check clubs page for music/arts groups
        clubs_content = self._pages.get(self.CLUBS_URL, "")
        combined = (content or "") + " " + (clubs_content or "")

        if not combined.strip():
            self.data.warnings.append("Could not fetch arts or clubs pages for arts extraction")
            return

        # Music ensembles (from arts-culture page + clubs page)
        music_groups = {
            "Concert Band": "Concert Band",
            "Wind Band": "Wind Band",
            "Jazz Band": "Jazz Band",
            "String Ensemble": "String Ensemble",
            "Rock Programme": "Rock Programme",
            "Chamber Ensemble": "Chamber Ensembles",
            "Tira Waiata o Taurere": "Tira Waiata o Taurere Choir",  # auditioned GDC choir
        }
        for search_term, display_name in music_groups.items():
            if search_term.lower() in combined.lower():
                self.data.arts.append(display_name)

        # Non-auditioned choir
        if re.search(r'choir.*all\s*comers|non.?auditioned.*choir', combined, re.IGNORECASE):
            self.data.arts.append("Choir")

        # Drama / performance
        drama_groups = ["Theatresports"]
        for group in drama_groups:
            if group.lower() in combined.lower():
                self.data.arts.append(group)

        # Dance groups
        dance_groups = {
            "Senior Co-curricular Dance": "Senior Dance Group",
            "Junior Co-curricular Dance": "Junior Dance Group",
            "K-Pop Dance": "K-Pop Dance Group",
            "Asian Fusion Dance": "Asian Fusion Dance Group",
        }
        for search_term, display_name in dance_groups.items():
            if search_term.lower() in combined.lower():
                self.data.arts.append(display_name)

        # Kapa Haka
        if re.search(r'kapa\s*haka', combined, re.IGNORECASE):
            self.data.arts.append("Kapa Haka")

    # ── Clubs ─────────────────────────────────────────

    def extract_clubs(self):
        """Extract clubs from clubs & groups page."""
        self.data.clubs_url = self.CLUBS_URL
        content = self._pages.get(self.CLUBS_URL, "")
        if not content:
            self.data.warnings.append("Could not fetch clubs page")
            return

        # From clubs-groups page — excludes arts/sports items
        # (Choir, Concert Band, Jazz Band, String Ensemble, Wind Band, Theatresports,
        #  dance groups, Kapa Haka, Sport → already in arts/sports)
        self.data.clubs = [
            "Amnesty International",
            "Arts Club",
            "Book Club",
            "Chess Club",
            "Coding Club",
            "Craft Club",
            "Cultural Club",
            "Debating",
            "Duke of Edinburgh",
            "Dungeons and Dragons / Tabletop",
            "E Pro 8 Club",
            "Fantasy Football",
            "Homework Club",
            "Interact",
            "Junior Maths Club",
            "Lighting Crew",
            "Mahjong Club",
            "Maker Space / Future Problem Solving Club",
            "Play Reading Group",
            "Poetry Writing Club",
            "Polyfest Speech Group",
            "Queer Support",
            "Rangatahi Ora",
            "Reading Competitions",
            "Space Club",
            "Spoken Word Poetry Club",
            "Student Librarians",
            "Sustainability Group",
            "TECHS",
            "The Fish",
            "UN Youth",
            "Writer's Circle",
            "Young Enterprise Scheme",
        ]

    # ── Fees ──────────────────────────────────────────

    def extract_fees(self):
        """Fees not publicly listed on GDC international page."""
        self.data.intl_fees_url = self.INTL_URL
        # International page does not display fee amounts — only contact info
        # Leave fees as None with a warning
        self.data.warnings.append(
            "International fees not publicly listed on website — contact school for amounts"
        )

    # ── Curriculum ────────────────────────────────────

    def extract_curriculum(self):
        """GDC offers NCEA + IB MYP (Middle Years Programme for Years 9-10)."""
        self.data.curriculum_systems = [
            {
                "system": "NCEA",
                "status": "offered",
                "evidence_url": "https://www.gdc.school.nz/explore-glendowie-college/academic/year-11-pathway",
            },
            {
                "system": "IB",
                "status": "offered",
                "evidence_url": "https://www.gdc.school.nz/explore-glendowie-college/academic/years-9-10-myp",
            },
        ]

    # ── Logo ──────────────────────────────────────────

    def extract_logo(self):
        # Vertical SVG logo from SchoolBridge CDN
        self.data.logo_url = "https://gdc.ibcdn.nz/media/2025_03_11_glendowie-logo-vert.svg"

    # ── Zone ──────────────────────────────────────────

    def extract_zone(self):
        self.data.zone_page_url = self.ZONE_URL
