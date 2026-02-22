"""
scrapers/base_scraper.py

Thin wrapper around Crawl4AI's AsyncWebCrawler.
All concrete scrapers inherit from BaseScraper.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

from scrapers.config import REQUEST_DELAY_SECONDS

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    Abstract base class for all scrapers in this project.

    Subclasses must implement:
        - ``source_name``  (str property)  – human-readable identifier
        - ``seed_urls``    (list[str] property) – starting URLs for the crawl
        - ``parse``        (coroutine) – extracts structured records from a CrawlResult
    """

    # ------------------------------------------------------------------ #
    # Abstract interface
    # ------------------------------------------------------------------ #

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique identifier for this source (e.g. 'protothema')."""

    @property
    @abstractmethod
    def seed_urls(self) -> list[str]:
        """List of entry-point URLs to crawl."""

    @abstractmethod
    async def parse(self, result) -> list[dict]:
        """
        Convert a raw CrawlResult into a list of structured record dicts.
        Each dict should conform to the project's output schema (see README).
        """

    # ------------------------------------------------------------------ #
    # Crawl4AI browser / run configuration
    # ------------------------------------------------------------------ #

    def _browser_config(self) -> BrowserConfig:
        return BrowserConfig(
            headless=True,
            verbose=False,
        )

    def _run_config(self) -> CrawlerRunConfig:
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,       # always fetch fresh content
            page_timeout=30_000,               # ms
            wait_until="domcontentloaded",
            word_count_threshold=50,           # skip near-empty pages
        )

    # ------------------------------------------------------------------ #
    # Public crawl entry-point
    # ------------------------------------------------------------------ #

    async def crawl(self) -> list[dict]:
        """
        Run the scraper against all seed URLs and return a flat list of records.
        Applies a polite delay between successive requests.
        """
        all_records: list[dict] = []

        async with AsyncWebCrawler(config=self._browser_config()) as crawler:
            for i, url in enumerate(self.seed_urls):
                if i > 0:
                    await asyncio.sleep(REQUEST_DELAY_SECONDS)

                logger.info("[%s] Crawling %s", self.source_name, url)
                try:
                    result = await crawler.arun(url=url, config=self._run_config())
                    if result.success:
                        records = await self.parse(result)
                        all_records.extend(records)
                        logger.info(
                            "[%s] %s → %d records extracted",
                            self.source_name,
                            url,
                            len(records),
                        )
                    else:
                        logger.warning(
                            "[%s] Failed to crawl %s: %s",
                            self.source_name,
                            url,
                            result.error_message,
                        )
                except Exception as exc:
                    logger.error(
                        "[%s] Exception while crawling %s: %s",
                        self.source_name,
                        url,
                        exc,
                        exc_info=True,
                    )

        return all_records
