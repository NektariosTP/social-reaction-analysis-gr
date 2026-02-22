"""
scrapers/news/protothema.py

Spider for https://www.protothema.gr — Greek online news portal.
Inherits shared extraction logic from BaseNewsSpider and can be extended
with site-specific CSS selectors as the site structure is mapped out.
"""

from __future__ import annotations

from crawl4ai import CrawlResult

from scrapers.news.base_news_spider import BaseNewsSpider
from scrapers.config import NEWS_SOURCES

# Locate this source's config entry by name
_SOURCE_CFG = next(s for s in NEWS_SOURCES if s["name"] == "protothema")


class ProtothemaScraper(BaseNewsSpider):
    """
    Scraper for protothema.gr.

    Currently uses the default heuristic extraction from BaseNewsSpider.
    As the site's HTML structure is mapped, override ``_extract_articles``
    below with precise CSS selectors for article title, body, and date.
    """

    @property
    def source_name(self) -> str:
        return "protothema"

    @property
    def seed_urls(self) -> list[str]:
        return _SOURCE_CFG["seed_urls"]

    # ------------------------------------------------------------------
    # Optional: site-specific article extraction
    # Uncomment and implement once the HTML structure has been validated.
    # ------------------------------------------------------------------
    # def _extract_articles(self, result: CrawlResult) -> list[dict]:
    #     from bs4 import BeautifulSoup
    #     from datetime import datetime, timezone
    #
    #     soup = BeautifulSoup(result.html, "lxml")
    #     articles = []
    #     now = datetime.now(timezone.utc).isoformat()
    #
    #     for item in soup.select("article.article-item"):
    #         title_el = item.select_one("h3.title a")
    #         if not title_el:
    #             continue
    #
    #         articles.append({
    #             "source": self.source_name,
    #             "url": title_el.get("href", result.url),
    #             "title": title_el.get_text(strip=True),
    #             "body": "",          # fetched in a second-pass crawl
    #             "published_at": None,
    #             "scraped_at": now,
    #             "lang": "el",
    #             "category_hint": None,
    #         })
    #
    #     return articles
