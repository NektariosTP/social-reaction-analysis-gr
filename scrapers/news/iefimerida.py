"""
scrapers/news/iefimerida.py

Spider for https://www.iefimerida.gr — Greek online news portal.
Inherits shared extraction logic from BaseNewsSpider and can be extended
with site-specific CSS selectors as the site structure is mapped out.
"""

from __future__ import annotations

from scrapers.news.base_news_spider import BaseNewsSpider
from scrapers.config import NEWS_SOURCES

_SOURCE_CFG = next(s for s in NEWS_SOURCES if s["name"] == "iefimerida")


class IefimeriadaScraper(BaseNewsSpider):
    """
    Scraper for iefimerida.gr.

    Currently uses the default heuristic extraction from BaseNewsSpider.
    Override ``_extract_articles`` for site-specific CSS/XPath selectors
    once the HTML structure has been mapped.
    """

    @property
    def source_name(self) -> str:
        return "iefimerida"

    @property
    def seed_urls(self) -> list[str]:
        return _SOURCE_CFG["seed_urls"]
