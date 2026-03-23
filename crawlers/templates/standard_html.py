"""
Standard HTML crawler template.

For schools with simple static HTML websites (no JS rendering needed).
Examples: Rangitoto College, Westlake Boys, Macleans College.

Uses Scrapling Fetcher for HTTP requests.
"""

from .base import BaseCrawler


class StandardHtmlCrawler(BaseCrawler):
    """
    Template for standard HTML school websites.

    Subclasses (per-school scripts) override extract_* methods
    with school-specific selectors and URLs.
    """

    SITE_TYPE = "standard_html"

    def discover_pages(self):
        """Fetch homepage and discover key pages from navigation."""
        if not self.website:
            self.data.warnings.append("No website URL in database")
            return
        content = self.fetch_page(self.website)
        if not content:
            self.data.warnings.append(f"Failed to fetch homepage: {self.website}")

    # Default implementations — subclasses should override these
    # with school-specific logic.

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
