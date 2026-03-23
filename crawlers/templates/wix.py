"""
Wix crawler template.

For schools using Wix-based websites (JS-rendered).
Examples: Avondale College.

Key difference: Must use Playwright for dynamic rendering.
Scrapling Fetcher only gets JS scaffold code.
"""

import time

from .base import BaseCrawler


class WixCrawler(BaseCrawler):
    """
    Template for Wix school websites.

    Uses Playwright sync API for JavaScript rendering.
    Browser instance is reused across all fetches within a single crawl() call.
    Wait strategy: domcontentloaded + sleep(5) — not networkidle
    (Wix keeps firing network requests indefinitely).
    """

    SITE_TYPE = "wix"

    def __init__(self, school_number: int):
        super().__init__(school_number)
        self._playwright = None
        self._browser = None

    def _ensure_browser(self):
        """Start Playwright browser if not already running."""
        if self._browser is None:
            from playwright.sync_api import sync_playwright
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=True)

    def _close_browser(self):
        """Clean up Playwright resources."""
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None

    def _do_fetch(self, url: str) -> str:
        """Fetch using Playwright for JS rendering. Reuses browser instance."""
        try:
            self._ensure_browser()
            page = self._browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(5)  # Wix needs time to render
            text = page.inner_text("body")
            page.close()
            return text
        except Exception as e:
            print(f"  [WARN] Playwright fetch failed for {url}: {e}")
            # Fallback to regular HTTP
            return super()._do_fetch(url)

    def crawl(self, *args, **kwargs):
        """Override crawl to ensure browser cleanup after crawl completes."""
        try:
            return super().crawl(*args, **kwargs)
        finally:
            self._close_browser()

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
