"""
Epsom Girls Grammar School (School #64) — Standard HTML

Website: https://www.eggs.school.nz
Site type: Standard HTML (custom-built)
Sources:
  - Subjects: /eggs-life/academic-learning/years-9-10/ (Years 11-13 in image, not scrapable)
  - Sports: /eggs-life/co-curricular/sports/
  - Arts: /eggs-life/co-curricular/arts-and-culture/
  - Fees: /international-students/ (fees not directly listed, may need PDF)
  - Zone: /enrolments/zoning/zoning-map/
"""

import re

from ..templates.standard_html import StandardHtmlCrawler


class EggsCrawler(StandardHtmlCrawler):

    BASE = "https://www.eggs.school.nz"
    SUBJECTS_URL = "https://www.eggs.school.nz/eggs-life/academic-learning/years-9-10/"
    SPORTS_URL = "https://www.eggs.school.nz/eggs-life/co-curricular/sports/"
    ARTS_URL = "https://www.eggs.school.nz/eggs-life/co-curricular/arts-and-culture/"
    MUSIC_URL = "https://www.eggs.school.nz/eggs-life/co-curricular/music/"
    INTL_URL = "https://www.eggs.school.nz/international-students/applications/fees/"
    ZONE_URL = "https://www.eggs.school.nz/enrolments/zoning/"

    def discover_pages(self):
        """Fetch homepage and known source pages."""
        super().discover_pages()
        for url in [self.SUBJECTS_URL, self.SPORTS_URL, self.ARTS_URL, self.MUSIC_URL, self.INTL_URL, self.ZONE_URL]:
            self.fetch_page(url)

    Y11_13_URL = "https://www.eggs.school.nz/eggs-life/academic-learning/years-11-13/"

    Y11_13_URL = "https://www.eggs.school.nz/eggs-life/academic-learning/years-11-13/"

    # Mapping: raw name from website → pool name
    # Used when the school uses a different name than subject_pool
    SUBJECT_MAPPING = {
        "Earth & Space Science": "Earth and Space Science",  # & vs and
        "Samoan": "Gagana Samoa",           # pool uses Māori name
        "Travel & Tourism": "Tourism",      # pool just has Tourism
        "Visual Art": "Visual Arts",        # singular vs plural (pool is group)
    }

    # Subjects to SKIP — not standalone subjects, are sub-topics of other subjects
    SUBJECT_SKIP = {
        "Art Design",               # → sub-type of Visual Arts, not a pool subject
        "Calculus",                  # → Mathematics branch
        "Design Technology",        # → coarse name, EGGS has finer subjects (Digital Tech, Food Tech, etc.)
        "Literacy",                 # → not a standalone subject
        "Mathematics with Numeracy", # → Mathematics variant
        "Printmaking",              # → Visual Arts sub-type, user declined adding to pool
        "Sports Science",           # → not a standard NZQA subject
        "Statistics",               # → Mathematics branch
        "Writing for Publication",  # → English branch
    }

    def extract_subjects(self):
        """Extract subjects from Years 9-10 page + Years 11-13 image."""
        self.data.subjects_url = self.SUBJECTS_URL

        # Combined subjects from Year 9-10 text page AND Year 11-13 image
        # Year 11-13 image: Year-11-13-subjects-2026.png (manually read)
        all_subjects = [
            # Year 9-10 (from text page)
            "English", "Mathematics", "Science", "Social Studies",
            "Physical Education", "Health",
            "Chinese", "French", "Japanese", "Spanish", "Te Reo Maori",
            "Drama", "Music",
            "Design Technology", "Design & Visual Communication",
            "Digital Technology", "Food Technology", "Textiles",
            "Business Studies", "Philosophy",
            "ESOL",
            # Year 11-13 additional subjects (from image)
            "Accounting", "Art History",
            "Biology",
            "Chemistry", "Classical Studies",
            "Dance", "Earth & Space Science", "Economics",
            "Education for Sustainability",
            "Geography", "History",
            "Hospitality",
            "Legal Studies",
            "Media Studies",
            "Painting", "Photography", "Physics", "Printmaking",
            "Samoan", "Sculpture",
            "Tourism",
            "Travel & Tourism",
            "Visual Art",
        ]

        seen = set()
        for raw_name in all_subjects:
            if raw_name in self.SUBJECT_SKIP:
                continue
            # Map to pool name if alias exists
            pool_name = self.SUBJECT_MAPPING.get(raw_name, raw_name)
            key = pool_name.lower()
            if key not in seen:
                seen.add(key)
                self.data.subjects.append({
                    "name": pool_name,
                    "raw_name": raw_name,
                    "confidence": 0.9,
                    "source_url": self.SUBJECTS_URL if raw_name in [
                        "English", "Mathematics", "Science", "Social Studies",
                        "Physical Education", "Health", "Chinese", "French",
                        "Japanese", "Spanish", "Te Reo Maori", "Drama", "Music",
                        "Design Technology", "Design & Visual Communication",
                        "Digital Technology", "Food Technology", "Textiles",
                        "Business Studies", "Philosophy", "ESOL",
                    ] else self.Y11_13_URL,
                })

    def extract_sports(self):
        """Extract sports from co-curricular sports page."""
        self.data.sports_url = self.SPORTS_URL
        content = self._pages.get(self.SPORTS_URL, "")
        if not content:
            self.data.warnings.append("Could not fetch sports page")
            return

        known_sports = [
            "Adventure Racing", "Archery", "Athletics", "Badminton", "Basketball",
            "Cheerleading", "Chinese Martial Arts", "Cricket", "Cross Country",
            "Curling", "Cycling", "Distance Squad", "Dragon Boating", "Equestrian",
            "Fencing", "Football", "Futsall", "Golf", "Gym Sports", "Hockey",
            "Ki O Rahi", "Kilikiti", "Lacrosse", "Lifesaving",
            "Mountain Biking", "Netball", "Orienteering", "Rowing", "Rugby",
            "Skateboarding", "Snow Sports", "Softball", "Squash", "Swimming",
            "Table Tennis", "Tennis", "Touch", "Triathlon/Duathlon/Aquathon", "Ultimate Frisbee",
            "Underwater Hockey", "Volleyball", "Waka Ama", "Water Polo",
            "Weightlifting", "Yachting",
        ]
        for sport in known_sports:
            if sport.lower() in content.lower():
                self.data.sports.append(sport)

    def extract_arts(self):
        """Extract performing arts from arts & culture page + music page."""
        self.data.arts_url = self.ARTS_URL
        arts_content = self._pages.get(self.ARTS_URL, "")
        music_content = self._pages.get(self.MUSIC_URL, "")

        if not arts_content:
            self.data.warnings.append("Could not fetch arts page")

        # Drama / performance groups (from arts & culture page)
        known_drama = [
            "Drama Committee", "Theatre Company", "Theatresports",
            "Kapa Haka", "Showquest", "Sheilah Winn Shakespeare",
        ]
        for item in known_drama:
            if arts_content and item.lower() in arts_content.lower():
                self.data.arts.append(item)

        # Music ensembles (from music page)
        if not music_content:
            self.data.warnings.append("Could not fetch music page")
            return

        known_music = [
            "Paradisum", "Luminoso", "Fiorente", "Leogato",
            "Symphonia", "Chamber Orchestra", "String Ensemble",
            "Intermediate Concert Band", "Concert Band",
            "Stage Band", "Rock Bands", "Chamber Music",
        ]
        for item in known_music:
            if item.lower() in music_content.lower():
                self.data.arts.append(item)

    def extract_clubs(self):
        """Extract clubs from arts & culture page."""
        self.data.clubs_url = self.ARTS_URL
        content = self._pages.get(self.ARTS_URL, "")
        if not content:
            return

        known_clubs = [
            "Debating", "Megaschools", "Photography",
            "Slam Poetry", "Technical Team", "Visual Arts Club",
            "Writing Committee",
        ]
        for club in known_clubs:
            if club.lower() in content.lower():
                self.data.clubs.append(club)

        # Cultural groups (not arts, not sports → clubs)
        cultural_groups = [
            "Chinese", "Cook Island", "Fijian", "Filipino", "Gaelic",
            "Indian", "Japanese", "Korean", "Middle Eastern", "Niue",
            "Samoan", "Sri Lankan", "Thai", "Tongan",
        ]
        for group in cultural_groups:
            group_name = f"{group} Cultural Group"
            if group.lower() in content.lower():
                self.data.clubs.append(group_name)

    def extract_fees(self):
        """Extract international fees from fees page."""
        self.data.intl_fees_url = self.INTL_URL
        content = self._pages.get(self.INTL_URL, "")

        if content:
            # Extract fee year: look for "2026 Fees", "Fees 2026", "2026" near fees context
            year_match = re.search(r'(?:fees|tuition).*?(20\d{2})|(?:(20\d{2}).*?(?:fees|tuition))', content, re.IGNORECASE)
            if year_match:
                self.data.intl_fees_year = int(year_match.group(1) or year_match.group(2))

            # Look for tuition: "$23,000" or "23,000"
            tuition_match = re.search(r'\$\s*([\d,]+)', content)
            if tuition_match:
                amount = float(tuition_match.group(1).replace(",", ""))
                if 10000 < amount < 50000:  # sanity check for annual tuition range
                    self.data.intl_tuition_annual = amount

            # Look for homestay weekly: "$420" near "homestay" or "week"
            homestay_match = re.search(r'homestay.*?\$\s*([\d,]+)', content, re.IGNORECASE)
            if not homestay_match:
                homestay_match = re.search(r'\$\s*([\d,]+).*?(?:per\s*week|weekly|x\s*\d+\s*week)', content, re.IGNORECASE)
            if homestay_match:
                amount = float(homestay_match.group(1).replace(",", ""))
                if 200 < amount < 800:  # sanity check for weekly homestay range
                    self.data.intl_homestay_weekly = amount

        if not self.data.intl_tuition_annual:
            self.data.warnings.append("Could not extract tuition amount — needs manual entry")

    def extract_curriculum(self):
        """EGGS offers NCEA."""
        self.data.curriculum_systems = [
            {
                "system": "NCEA",
                "status": "offered",
                "evidence_url": "https://www.eggs.school.nz/eggs-life/academic-learning/academic-qualifications/",
            },
        ]

    def extract_logo(self):
        """EGGS logo from homepage."""
        self.data.logo_url = "https://www.eggs.school.nz/resources/assets/prod/6b1fc6a66d6a8af7f802bbd8f6395eb3.svg"

    def extract_zone(self):
        """EGGS enrolment zone info."""
        self.data.zone_page_url = "https://www.eggs.school.nz/enrolments/zoning/"
        self.data.zone_map_url = "https://www.eggs.school.nz/enrolments/zoning/zoning-map/"
