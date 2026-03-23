"""
WordPress crawler template.

For schools using WordPress websites.
Examples: Auckland Grammar School.

Key difference: CSS selectors may not work reliably.
Use page.body.decode() + regex for extraction.
"""

from .base import BaseCrawler


class WordPressCrawler(BaseCrawler):
    """
    Template for WordPress school websites.

    WordPress sites may return 200 but CSS selectors fail to match.
    Use raw body text + regex patterns instead.
    """

    SITE_TYPE = "wordpress"

    # WordPress uses the same requests-based fetch as BaseCrawler.
    # The raw HTML body works well for regex extraction on WP sites.

    def discover_pages(self):
        if not self.website:
            self.data.warnings.append("No website URL in database")
            return
        self.fetch_page(self.website)

    def extract_subjects(self):
        pass

    def extract_sports(self):
        pass

    def extract_arts(self):
        pass

    def extract_clubs(self):
        pass

    def extract_fees(self):
        pass

    def extract_curriculum(self):
        pass

    def extract_logo(self):
        pass

    def extract_zone(self):
        pass
