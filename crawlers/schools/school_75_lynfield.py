"""
Lynfield College (School #75) — Zeald CMS

Website: https://www.lynfield.school.nz
Site type: Zeald (custom CMS)
Sources:
  - Subjects: /Curriculum/Courses.html
  - Sports: /Extra-Curricular/Sports.html
  - Arts: /Extra-Curricular/Performing+Arts.html + /Extra-Curricular/Music.html
  - Clubs: /Extra-Curricular/Culture.html + /Extra-Curricular/Robotics.html
  - Fees: /International/Fees.html (2026, amounts in image — not scrapable)
  - Zone: /Enrolment/Enrolment+Zone.html
"""

import re

from ..templates.standard_html import StandardHtmlCrawler


class LynfieldCrawler(StandardHtmlCrawler):

    SITE_TYPE = "zeald"
    BASE = "https://www.lynfield.school.nz"
    COURSES_URL = "https://www.lynfield.school.nz/Curriculum/Courses.html"
    SPORTS_URL = "https://www.lynfield.school.nz/Extra-Curricular/Sports.html"
    PERFORMING_ARTS_URL = "https://www.lynfield.school.nz/Extra-Curricular/Performing+Arts.html"
    MUSIC_URL = "https://www.lynfield.school.nz/Extra-Curricular/Music.html"
    CULTURE_URL = "https://www.lynfield.school.nz/Extra-Curricular/Culture.html"
    INTL_FEES_URL = "https://www.lynfield.school.nz/International/Fees.html"
    ZONE_URL = "https://www.lynfield.school.nz/Enrolment/Enrolment+Zone.html"

    def discover_pages(self):
        super().discover_pages()
        for url in [self.COURSES_URL, self.SPORTS_URL, self.PERFORMING_ARTS_URL,
                    self.MUSIC_URL, self.CULTURE_URL, self.INTL_FEES_URL, self.ZONE_URL]:
            self.fetch_page(url)

    # ── Subjects ──────────────────────────────────────

    # Mapping: raw name from website → pool name
    SUBJECT_MAPPING = {
        "Te Reo": "Te Reo Maori",
        "Mandarin Chinese": "Chinese",
        "Visual Arts": "Painting",  # Visual Arts is a group; map to fine art subject
        "Music and Sound": "Music",
        "Health Education": "Health",
        "Automotive": "Materials and Processing Technology",
        "Carpentry": "Wood Technology",
        "Design and Visual Communication": "Design & Visual Communication",
        "Digital Technologies": "Digital Technology",
        "Fashion and Design": "Textiles",
        "Home Economics": "Food Technology",
        "Engineering": "Materials and Processing Technology",
        "Beauty Therapy": "Hospitality",  # closest pool match for vocational
        "Commerce": "Business Studies",
    }

    # Subjects to SKIP — not standalone pool subjects or duplicates
    SUBJECT_SKIP = {
        "Junior Science",       # → Science (already listed)
        "Level 1 Science",      # → Science variant
        "Level 2 Science",      # → Science variant
        "Level 3 Science",      # → Science variant
        "Junior Technology",    # → too generic
        "Sports Studies",       # → not a standard NZQA pool subject
        "Outdoor Education",    # → not in pool
        "Beauty Therapy",       # → vocational, not in pool
        "Commerce",             # → group; we have Accounting + Economics
    }

    def extract_subjects(self):
        """Extract subjects from Courses page."""
        self.data.subjects_url = self.COURSES_URL

        # From Courses.html — comprehensive list across all departments
        all_subjects = [
            # Creative Arts
            "Dance", "Drama", "Music and Sound", "Visual Arts",
            # Health and PE
            "Health Education", "Physical Education",
            # Languages
            "English", "ESOL", "Media Studies", "Te Reo",
            "German", "Japanese", "Mandarin Chinese", "Spanish",
            # Mathematics
            "Mathematics",
            # Science
            "Science",
            # Humanities and Commerce
            "Classical Studies", "Geography", "History", "Tourism",
            "Social Studies", "Accounting", "Economics",
            # Technology
            "Automotive", "Carpentry",
            "Design and Visual Communication", "Digital Technologies",
            "Early Childhood Education", "Electronics",
            "Engineering", "Fashion and Design", "Home Economics",
            "Hospitality",
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
                    "source_url": self.COURSES_URL,
                })

    # ── Sports ────────────────────────────────────────

    def extract_sports(self):
        """Extract sports from sports page — extensive summer + winter programme."""
        self.data.sports_url = self.SPORTS_URL
        content = self._pages.get(self.SPORTS_URL, "")
        if not content:
            self.data.warnings.append("Could not fetch sports page")
            return

        # From Sports.html — Summer + Winter inter-school sports
        known_sports = [
            # Summer
            "Cricket", "Volleyball", "Softball", "Kilikiti", "Touch", "Tag",
            "Golf", "Swimming", "Athletics", "Tennis", "Water Polo",
            "Lawn Bowls", "Dragon Boating", "Cycling", "Ultimate Frisbee",
            # Winter
            "Basketball", "Cross Country", "Rugby", "Football", "Badminton",
            "Rugby League", "Gymnastics", "Netball", "Squash", "Hockey",
            "Wrestling", "Table Tennis", "Curling", "Mountain Biking", "Lacrosse",
        ]
        for sport in known_sports:
            if sport.lower() in content.lower():
                self.data.sports.append(sport)

        # Check for 8-Ball Pool (listed on page as "8-Ball Pool")
        if re.search(r'8.?ball\s*pool', content, re.IGNORECASE):
            self.data.sports.append("8-Ball Pool")

        # Check for Futsal (intra-school)
        if "futsal" in content.lower():
            self.data.sports.append("Futsal")

    # ── Arts / Performing Arts ────────────────────────

    def extract_arts(self):
        """Extract performing arts from music page + performing arts page."""
        self.data.arts_url = self.MUSIC_URL
        music_content = self._pages.get(self.MUSIC_URL, "")
        perf_content = self._pages.get(self.PERFORMING_ARTS_URL, "")

        if not music_content:
            self.data.warnings.append("Could not fetch music page")
        if not perf_content:
            self.data.warnings.append("Could not fetch performing arts page")

        combined = (music_content or "") + " " + (perf_content or "")

        # Music ensembles from Music page
        music_groups = {
            "Concert Band": "Concert Band",
            "Big Band": "Big Band",
            "Symphony Orchestra": "Symphony Orchestra",
            "Chamber Orchestra": "Chamber Orchestra",
            "Jazz Combo": "Jazz Combo",
            "Premier Jazz Band": "Premier Jazz Band",
            "Standard Jazz Band": "Standard Jazz Band",
            "The Flock": "The Flock",
            "Chamber Groups": "Chamber Groups",
            "Choir": "Choir",
        }
        for search_term, display_name in music_groups.items():
            if search_term.lower() in combined.lower():
                self.data.arts.append(display_name)

        # Rock/Pop bands (junior + senior)
        if re.search(r'rock.?pop|rock/pop', combined, re.IGNORECASE):
            self.data.arts.append("Rock Bands")

        # Performing arts — Polyfest is a performance event
        if re.search(r'polyfest', combined, re.IGNORECASE):
            self.data.arts.append("Polyfest")

        # Kapa Haka — check both pages
        if re.search(r'kapa\s*haka', combined, re.IGNORECASE):
            self.data.arts.append("Kapa Haka")

    # ── Clubs ─────────────────────────────────────────

    def extract_clubs(self):
        """Extract clubs from culture page + performing arts page."""
        self.data.clubs_url = self.CULTURE_URL
        content = self._pages.get(self.CULTURE_URL, "")
        perf_content = self._pages.get(self.PERFORMING_ARTS_URL, "")
        combined = (content or "") + " " + (perf_content or "")

        if not combined.strip():
            self.data.warnings.append("Could not fetch culture or performing arts pages")
            return

        # From Performing Arts page
        clubs = []
        if re.search(r'debating|spoken\s*word', combined, re.IGNORECASE):
            clubs.append("Debating")

        # Cultural activities — international exchange programme
        # Culture page mentions cultural groups but no specific club names listed
        # Add what is confirmed from the pages
        if re.search(r'cultural.*festival|food.*entertainment', combined, re.IGNORECASE):
            clubs.append("Cultural Food and Entertainment Festival")

        # Robotics — has its own page
        clubs.append("Robotics")

        self.data.clubs = clubs

    # ── Fees ──────────────────────────────────────────

    def extract_fees(self):
        """Extract international fees — page says '2026' but amounts are in an image."""
        self.data.intl_fees_url = self.INTL_FEES_URL
        content = self._pages.get(self.INTL_FEES_URL, "")

        if content:
            # Page title says "International Student Fees 2026"
            # But actual fee amounts are in an image, not scrapable text
            # Try regex extraction in case some text is present
            tuition_match = re.search(r'\$\s*([\d,]+)', content)
            if tuition_match:
                amount = float(tuition_match.group(1).replace(",", ""))
                if 10000 < amount < 50000:
                    self.data.intl_tuition_annual = amount
                    self.data.intl_fees_year = 2026

            homestay_match = re.search(r'homestay.*?\$\s*([\d,]+)', content, re.IGNORECASE)
            if not homestay_match:
                homestay_match = re.search(r'\$\s*([\d,]+).*?(?:per\s*week|weekly)', content, re.IGNORECASE)
            if homestay_match:
                amount = float(homestay_match.group(1).replace(",", ""))
                if 200 < amount < 800:
                    self.data.intl_homestay_weekly = amount

        if not self.data.intl_tuition_annual:
            self.data.warnings.append(
                "International fees for 2026 exist but amounts are in image — "
                "download 'LC International Programme Fees 2026A' PDF for manual entry"
            )

    # ── Curriculum ────────────────────────────────────

    def extract_curriculum(self):
        """Lynfield College offers NCEA."""
        self.data.curriculum_systems = [
            {
                "system": "NCEA",
                "status": "offered",
                "evidence_url": "https://www.lynfield.school.nz/Curriculum/Assessment+and+NCEA.html",
            },
        ]

    # ── Logo ──────────────────────────────────────────

    def extract_logo(self):
        # Header logo from Zeald CDN — only logo available on site
        # Dimensions unknown; may be banner-style. Use as-is until square alternative found.
        self.data.logo_url = "https://zdn.nz/site/lynfieldcollege/images/basic_theme/logo1.png"

    # ── Zone ──────────────────────────────────────────

    def extract_zone(self):
        self.data.zone_page_url = self.ZONE_URL
