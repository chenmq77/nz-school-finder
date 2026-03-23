"""
Macleans College (School #41) — Standard HTML

Website: https://www.macleans.school.nz
Site type: Standard HTML
External sources:
  - Subjects: https://macleans.bridge.school.nz/course_selection/course_list
  - Sports: https://www.sporty.co.nz/macleanscol/Sport-1/Sport-1
  - Music: https://www.sporty.co.nz/macleanscol/Performing-Arts-1/PerformingArts2
  - Fees: https://www.macleans.school.nz/parent/student-enrolments/international
"""

import re

from ..templates.standard_html import StandardHtmlCrawler


class MacleansCrawler(StandardHtmlCrawler):

    SUBJECTS_URL = "https://macleans.bridge.school.nz/course_selection/course_list"
    SPORTS_URL = "https://www.sporty.co.nz/macleanscol/Sport-1/Sport-1"
    MUSIC_URL = "https://www.sporty.co.nz/macleanscol/Performing-Arts-1/PerformingArts2"
    FEES_URL = "https://www.macleans.school.nz/parent/student-enrolments/international"

    def discover_pages(self):
        """Fetch homepage and known external source pages."""
        super().discover_pages()
        # Fetch known external source pages
        for url in [self.SUBJECTS_URL, self.SPORTS_URL, self.MUSIC_URL, self.FEES_URL]:
            self.fetch_page(url)

    def extract_subjects(self):
        """Extract subjects from SchoolBridge course list."""
        self.data.subjects_url = self.SUBJECTS_URL
        content = self._pages.get(self.SUBJECTS_URL, "")
        if not content:
            self.data.warnings.append("Could not fetch subjects page")
            return

        # SchoolBridge course list has subject names in specific patterns
        # This is a simplified extraction — adjust selectors per actual HTML structure
        # Known subjects from previous crawl (verified):
        known_subjects = [
            "Accounting", "Biology", "Business Studies", "Chemistry", "Chinese",
            "Classical Studies", "Construction", "Design",
            "Design & Visual Communication", "Digital Technology", "Drama",
            "ESOL", "Early Childhood Education", "Economics", "English",
            "Food Technology", "Geography", "Health", "History", "Japanese",
            "Mathematics", "Media Studies", "Music", "Painting", "Photography",
            "Physical Education", "Physics", "Product Development", "Science",
            "Social Studies", "Spanish", "Te Reo Maori", "Textiles", "Tourism",
        ]

        for name in known_subjects:
            if name.lower() in content.lower():
                self.data.subjects.append({
                    "name": name,
                    "raw_name": name,
                    "confidence": 0.9,
                    "source_url": self.SUBJECTS_URL,
                })

    def extract_sports(self):
        """Extract sports from Sporty.co.nz page."""
        self.data.sports_url = self.SPORTS_URL
        content = self._pages.get(self.SPORTS_URL, "")
        if not content:
            self.data.warnings.append("Could not fetch sports page")
            return

        # Known sports from previous crawl:
        known_sports = [
            "Athletics", "Badminton", "Basketball", "Cricket", "Cycling",
            "Fencing", "Football", "Golf", "Hockey", "Mountain Biking",
            "Netball", "Orienteering", "Rowing", "Rugby", "Snow Sports",
            "Squash", "Table Tennis", "Tennis", "Touch Rugby", "Volleyball",
            "Water Polo",
        ]
        for sport in known_sports:
            if sport.lower() in content.lower():
                self.data.sports.append(sport)

    def extract_arts(self):
        """Extract performing arts from Sporty.co.nz page."""
        self.data.arts_url = self.MUSIC_URL
        content = self._pages.get(self.MUSIC_URL, "")
        if not content:
            self.data.warnings.append("Could not fetch music/arts page")
            return

        known_music = [
            "Symphony Orchestra", "Sinfonietta", "Chamber Orchestra",
            "Concert Band", "Symphonic Band", "Chamber Music", "Chorale",
            "Aria", "Knights of the Castle", "Musical Production",
            "Drama Production", "Showquest", "Shakespeare Festival",
            "Kapa Haka",
        ]
        for item in known_music:
            if item.lower() in content.lower():
                self.data.arts.append(item)

    def extract_clubs(self):
        """Extract clubs and activities."""
        known_clubs = [
            "Art Exhibitions", "Debating", "Interact Club",
            "Intercultural Club", "Speech Competitions",
            "Stage Challenge", "Wearable Arts",
        ]
        for club in known_clubs:
            self.data.clubs.append(club)
        self.data.clubs_url = self.website

    def extract_fees(self):
        """Extract international student fees."""
        self.data.intl_fees_url = self.FEES_URL
        content = self._pages.get(self.FEES_URL, "")
        if not content:
            self.data.warnings.append("Could not fetch fees page")
            return

        # Look for tuition amount pattern
        tuition_match = re.search(r'\$\s*([\d,]+)\s*(?:per\s*(?:year|annum))?', content)
        if tuition_match:
            self.data.intl_tuition_annual = float(tuition_match.group(1).replace(",", ""))
        else:
            self.data.warnings.append("Could not extract tuition amount — needs manual entry")

        # Homestay
        homestay_match = re.search(r'homestay.*?\$\s*([\d,]+)\s*(?:per\s*week)?', content, re.IGNORECASE)
        if homestay_match:
            self.data.intl_homestay_weekly = float(homestay_match.group(1).replace(",", ""))
        else:
            self.data.warnings.append("Could not extract homestay amount — needs manual entry")

    def extract_curriculum(self):
        """Extract curriculum systems offered."""
        self.data.curriculum_systems = [
            {
                "system": "NCEA",
                "status": "offered",
                "evidence_url": "https://www.macleans.school.nz/learning/ncea",
            },
        ]

    def extract_logo(self):
        """Macleans logo."""
        self.data.logo_url = "https://www.macleans.school.nz/img/logo.png"

    def extract_zone(self):
        """Macleans enrolment zone info."""
        pass  # Zone info not yet identified for Macleans
