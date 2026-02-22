"""
scrapers/news/base_news_spider.py

Base class shared by all news website spiders.
Provides common article-extraction logic and applies a keyword filter
to discard pages that are clearly unrelated to social reactions.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from crawl4ai import CrawlResult

from scrapers.base_scraper import BaseScraper
from scrapers.config import REACTION_KEYWORDS


def _contains_keyword(text: str) -> bool:
    """Return True if *text* contains at least one Greek reaction keyword (case-insensitive)."""
    lowered = text.lower()
    return any(kw.lower() in lowered for kw in REACTION_KEYWORDS)


def _clean_text(raw: str) -> str:
    """Strip excessive whitespace from a raw string."""
    return re.sub(r"\s+", " ", raw).strip()


class BaseNewsSpider(BaseScraper):
    """
    Extends BaseScraper with shared behaviour for Greek news sites.

    parse() attempts heuristic extraction of article metadata from the
    CrawlResult and applies a keyword filter so only relevant content
    reaches the storage layer.

    Subclasses may override ``_extract_articles`` for site-specific logic.
    """

    async def parse(self, result: CrawlResult) -> list[dict]:
        articles = self._extract_articles(result)
        relevant = [a for a in articles if _contains_keyword(a.get("title", "") + " " + a.get("body", ""))]
        return relevant

    def _extract_articles(self, result: CrawlResult) -> list[dict]:
        """
        Default extraction strategy: treat the full page as one article.
        Subclasses should override this with site-specific CSS/XPath selectors.
        """
        now = datetime.now(timezone.utc).isoformat()
        title = result.metadata.get("title", "") if result.metadata else ""
        body = _clean_text(result.markdown or "")

        record = {
            "source": self.source_name,
            "url": result.url,
            "title": _clean_text(title),
            "body": body,
            "published_at": None,   # override in subclass when available
            "scraped_at": now,
            "lang": "el",
            "category_hint": None,
        }
        return [record] if record["title"] or record["body"] else []
