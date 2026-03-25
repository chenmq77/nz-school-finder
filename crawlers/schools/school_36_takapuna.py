"""
Takapuna Grammar School (School #36) — Next.js

Website: https://www.takapuna.school.nz
Site type: Next.js (server-rendered React)
Sources:
  - Subjects: /curriculum-and-learning/subjects/ (department pages with sub-pages)
  - Sports: sporty.co.nz/takapunagrammar/Our-Sports/sports-2 (primary, may 403)
            gotonewzealand.co.nz/takapuna-grammar-school/ (fallback, comma list)
  - Arts: /student-life/performing-arts/
  - Clubs: /student-life/co-curricular-clubs/
  - Fees: /international/ (fees not publicly listed)
  - Zone: /our-school/enrolments/
"""

import re

from ..templates.standard_html import StandardHtmlCrawler


class TakapunaCrawler(StandardHtmlCrawler):

    SITE_TYPE = "nextjs"
    BASE = "https://www.takapuna.school.nz"
    SUBJECTS_URL = "https://www.takapuna.school.nz/curriculum-and-learning/subjects/"
    SPORTS_URL = "https://www.sporty.co.nz/takapunagrammar/Our-Sports/sports-2"
    ARTS_URL = "https://www.takapuna.school.nz/student-life/performing-arts/"
    CLUBS_URL = "https://www.takapuna.school.nz/student-life/co-curricular-clubs/"
    INTL_URL = "https://www.takapuna.school.nz/international/"
    IB_URL = "https://www.takapuna.school.nz/curriculum-and-learning/international-baccalaureate/"
    ZONE_URL = "https://www.takapuna.school.nz/our-school/enrolments/"

    # Sub-pages for detailed subject extraction
    SUBJECTS_ART_URL = "https://www.takapuna.school.nz/curriculum-and-learning/subjects/art/"
    SUBJECTS_LANG_URL = "https://www.takapuna.school.nz/curriculum-and-learning/subjects/languages/"
    SUBJECTS_SCI_URL = "https://www.takapuna.school.nz/curriculum-and-learning/subjects/science/"
    SUBJECTS_SOC_URL = "https://www.takapuna.school.nz/curriculum-and-learning/subjects/social-sciences/"
    SUBJECTS_TECH_URL = "https://www.takapuna.school.nz/curriculum-and-learning/subjects/technology/"
    SUBJECTS_ENG_URL = "https://www.takapuna.school.nz/curriculum-and-learning/subjects/english/"
    SUBJECTS_PERF_URL = "https://www.takapuna.school.nz/curriculum-and-learning/subjects/performing-arts/"
    SUBJECTS_PE_URL = "https://www.takapuna.school.nz/curriculum-and-learning/subjects/pe-and-health/"

    def discover_pages(self):
        super().discover_pages()
        for url in [self.SUBJECTS_URL, self.SPORTS_URL, self.ARTS_URL,
                    self.CLUBS_URL, self.INTL_URL, self.IB_URL, self.ZONE_URL,
                    self.SUBJECTS_ART_URL, self.SUBJECTS_LANG_URL,
                    self.SUBJECTS_SCI_URL, self.SUBJECTS_SOC_URL,
                    self.SUBJECTS_TECH_URL, self.SUBJECTS_ENG_URL,
                    self.SUBJECTS_PERF_URL, self.SUBJECTS_PE_URL]:
            self.fetch_page(url)

    # ── Subjects ──────────────────────────────────────

    # Mapping: raw name from website → pool name
    SUBJECT_MAPPING = {
        "Te Reo Māori": "Te Reo Maori",
        "Building and Construction": "Construction",
        "Product Design": "Product Development",
        "Computer Science": "Digital Technology",
        "Spatial Design": "Design & Visual Communication",  # "formally DVC"
        "Textile Design": "Textiles",
    }

    # Subjects to SKIP — not standalone pool subjects
    SUBJECT_SKIP = {
        "English Internal",     # → English variant, not separate pool subject
    }

    def extract_subjects(self):
        """Extract subjects from department sub-pages."""
        self.data.subjects_url = self.SUBJECTS_URL

        # Compiled from individual department pages:
        # English: English, Media Studies (+ English Internal skipped)
        # Languages: Chinese, Spanish, Te Reo Māori, Japanese, French
        # Science: Biology, Chemistry, Physics
        # Social Sciences: Classical Studies, History, Geography, Tourism
        # Technology: Building and Construction, Product Design, Computer Science,
        #             Hospitality, Spatial Design (DVC), Textile Design
        # Performing Arts: Dance, Drama, Music
        # PE & Health: Physical Education, Health
        # Art: Painting (mapped from "Art")
        # Mathematics: Mathematics
        all_subjects = [
            # English department
            "English", "Media Studies",
            # Languages
            "Chinese", "Spanish", "Te Reo Māori", "Japanese", "French",
            # Science
            "Biology", "Chemistry", "Physics", "Science",
            # Social Sciences
            "Classical Studies", "History", "Geography", "Tourism",
            # Technology
            "Building and Construction", "Product Design", "Computer Science",
            "Hospitality", "Spatial Design", "Textile Design",
            # Performing Arts (as academic subjects)
            "Dance", "Drama", "Music",
            # PE & Health
            "Physical Education", "Health",
            # Art
            "Painting",
            # Mathematics
            "Mathematics",
            # Other
            "ESOL",
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
        """Extract sports from Sporty sports-2 page (icon grid) + Other Sports.

        Pages render sport icons via JS (Cloudflare-protected), not parseable
        by requests. Lists verified via Playwright screenshots on 2026-03-25.
        Sources:
          sporty.co.nz/takapunagrammar/Our-Sports/sports-2  (main grid)
          sporty.co.nz/additionalsports                     (Other Sports)
        """
        self.data.sports_url = self.SPORTS_URL

        # 18 sports from main icon grid
        sports = [
            "Athletics", "Badminton", "Basketball", "Cricket",
            "Cycling", "Football", "Hockey", "Rowing",
            "Rugby", "Sailing", "Squash", "Swimming",
            "Table Tennis", "Tennis", "Touch", "Ultimate Frisbee",
            "Volleyball", "Water Polo",
        ]
        # 14 from "Other Sports" page (sporty.co.nz/additionalsports)
        other_sports = [
            "Archery", "Cross Country", "Diving", "Equestrian",
            "Golf", "Gymnastics", "Trampolining", "Karate",
            "Mountain Biking", "Orienteering", "Rock Climbing",
            "Snow Sports", "Surfing", "Synchronised Swimming",
            "Triathlon",
        ]
        for sport in sports + other_sports:
            self.data.sports.append(sport)

    # ── Arts / Performing Arts ────────────────────────

    def extract_arts(self):
        """Extract performing arts from performing-arts page."""
        self.data.arts_url = self.ARTS_URL
        content = self._pages.get(self.ARTS_URL, "")
        if not content:
            self.data.warnings.append("Could not fetch performing arts page")
            return

        # Dance companies
        dance_groups = {
            "Cactus Dance": "Cactus Dance Company",
            "Tempus Dance": "Tempus Dance Company",
        }
        for search_term, display_name in dance_groups.items():
            if search_term.lower() in content.lower():
                self.data.arts.append(display_name)

        # Music ensembles
        music_groups = {
            "Concert Band": "Concert Band",
            "Development Concert Band": "Development Concert Band",
            "Jazz Band": "Jazz Band",
            "Orchestra": "Orchestra",
            "Rock Bands": "Rock Bands",
            "Chamber Groups": "Chamber Groups",
        }
        for search_term, display_name in music_groups.items():
            if search_term.lower() in content.lower():
                self.data.arts.append(display_name)

        # Choirs — names don't obviously indicate choir, add suffix
        choirs = {
            "Leonessa": "Leonessa Choir",
            "Chorale": "Chorale Choir",
        }
        for search_term, display_name in choirs.items():
            if search_term.lower() in content.lower():
                self.data.arts.append(display_name)

        # Theatre
        theatre_groups = ["Theatresports"]
        for group in theatre_groups:
            if group.lower() in content.lower():
                self.data.arts.append(group)

        # Kapa Haka
        if re.search(r'kapa\s*haka', content, re.IGNORECASE):
            self.data.arts.append("Kapa Haka")

    # ── Clubs ─────────────────────────────────────────

    def extract_clubs(self):
        """Extract clubs from co-curricular clubs page — 48 clubs."""
        self.data.clubs_url = self.CLUBS_URL

        # From co-curricular-clubs page — comprehensive list
        # Excludes items already in arts (dance, music, theatre) and sports
        self.data.clubs = [
            "Alchemist Club",
            "Amnesty International",
            "Board Games Club",
            "Book Club",
            "Carpentry Extension - Boatbuilding",
            "Chinese Art Club",
            "Computer Coding Club",
            "Chess Club",
            "Classics Club",
            "Craft Club",
            "Debate Competition",
            "Duke of Edinburgh",
            "Electronics Club",
            "Enviro Club",
            "Epro8",
            "Esports Club",
            "Feminist Club",
            "Filipino Club",
            "Film Club",
            "Finance & Investment Club",
            "French Club",
            "Homework Club",
            "Japanese Club",
            "Japanese Cultural Dance Club",
            "Jesus Hub",
            "Journalism Club",
            "Latin Club",
            "Maths Olympiad & Competitions Club",
            "Medical Science Club",
            "Mock Trial Club",
            "Philosophy Club",
            "Photography Club",
            "Psychology Club",
            "Pottery Club",
            "Politics & Civics Club",
            "PureBio Club",
            "Queer-Straight Alliance",
            "Robotics Club",
            "Realism Painting Club",
            "Science & Engineering Club",
            "Sewing & Construction Club",
            "Spanish Club",
            "STEM Scholars Club",
            "Science Olympiad Club",
            "Scrapbooking Club",
            "Theatre & Literature Club",
            "UNICEF Club",
            "Video Games Club",
        ]

    # ── Fees ──────────────────────────────────────────

    def extract_fees(self):
        """Fees not publicly listed on TGS international page."""
        self.data.intl_fees_url = self.INTL_URL
        # International page does not display fee amounts
        # "Apply Now" link exists but no dollar figures shown
        self.data.warnings.append(
            "International fees not publicly listed on website — contact school for amounts"
        )

    # ── Curriculum ────────────────────────────────────

    def extract_curriculum(self):
        """TGS offers NCEA + IB Diploma Programme."""
        self.data.curriculum_systems = [
            {
                "system": "NCEA",
                "status": "offered",
                "evidence_url": "https://www.takapuna.school.nz/curriculum-and-learning/subjects/",
            },
            {
                "system": "IB",
                "status": "offered",
                "evidence_url": "https://www.takapuna.school.nz/curriculum-and-learning/international-baccalaureate/",
            },
        ]

    # ── Logo ──────────────────────────────────────────

    def extract_logo(self):
        # Next.js site uses inline SVG crest, no standalone image URL.
        # Sporty CDN hosts the school logo as PNG (15 KB).
        self.data.logo_url = "https://prodcdn.sporty.co.nz/cms/11754/logo.png"

    # ── Zone ──────────────────────────────────────────

    def extract_zone(self):
        self.data.zone_page_url = self.ZONE_URL
