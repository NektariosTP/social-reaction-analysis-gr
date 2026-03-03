"""
scrapers/news/eleftherostypos.py

Spider for https://www.eleftherostypos.gr — Greek online newspaper
(digital arm of «Ελεύθερος Τύπος»).

Crawl strategy — sitemap-driven (single flat sitemap):
  1. Fetch the single Google News sitemap at the configured ``sitemap_url``
     via Crawl4AI (Playwright).  The site is protected by Cloudflare; plain
     HTTP requests (httpx) are refused with 403.  Playwright bypasses the
     challenge automatically.
     eleftherostypos.gr uses a flat <urlset> file, but Cloudflare's XSLT
     renderer transforms the XML into an HTML table before the browser sees
     it.  Each table row contains:
       cell[0] — news title (inside an <a href="…"> whose href is the article URL)
       cell[1] — publication date in ISO 8601 format
     (The ``news:keywords`` field is not exposed in the XSLT output and is
     therefore unavailable; keyword pre-filtering runs on the title only.)
  2. Apply the reaction-keyword filter on the title *before* hitting any
     article URLs — avoids unnecessary browser crawls.
  3. Crawl only the matching article pages with Crawl4AI to retrieve body text.

Note on body-text extraction:
  eleftherostypos.gr is a custom CMS behind Cloudflare; only Playwright-based
  crawling can access fully rendered pages.  After Playwright hydration the
  relevant HTML structure is:

  Standfirst   : h2.ap-title          (subheading deck above body)
  Body wrapper : div.ap-article-text  (contains the article paragraphs)
  Content kept : p elements (no class) — bare text paragraphs
  Noise removed:
      div.adslot               — ad banner blocks (mobile + sticky)
      div.related-posts-by-tag — «ΔΙΑΒΑΣΤΕ ΕΠΙΣΗΣ» inline related-posts
      glomex-integration       — embedded video player widget
      script / style / iframe / noscript / figure
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, CrawlResult

from scrapers.news.base_news_spider import BaseNewsSpider, _contains_keyword, _clean_text
from scrapers.config import NEWS_SOURCES, REQUEST_DELAY_SECONDS

logger = logging.getLogger(__name__)

_SOURCE_CFG = next(s for s in NEWS_SOURCES if s["name"] == "eleftherostypos")
_SITEMAP_URL: str = _SOURCE_CFG["sitemap_url"]


# ---------------------------------------------------------------------------
# Spider
# ---------------------------------------------------------------------------

class EleftherotyposScraper(BaseNewsSpider):
    """
    Scraper for eleftherostypos.gr — single flat sitemap-driven strategy.

    Overrides ``crawl()`` from BaseScraper to implement a two-step pipeline:
      1. Fetch the flat Google News sitemap via Crawl4AI/Playwright (required
         because the site is behind Cloudflare; plain httpx is refused with 403).
         The sitemap is rendered as an HTML table by Cloudflare's XSLT transformer.
      2. Apply the reaction-keyword filter on the title (pre-crawl).
      3. Crawl matching article pages for body text via Crawl4AI.
    """

    @property
    def source_name(self) -> str:
        return "eleftherostypos"

    @property
    def seed_urls(self) -> list[str]:
        # Not used by this spider's crawl() override.
        # Required by the abstract BaseScraper interface.
        return []

    # ------------------------------------------------------------------
    # Public entry-point (overrides BaseScraper.crawl)
    # ------------------------------------------------------------------

    async def crawl(self) -> list[dict]:
        """
        Full sitemap-driven crawl pipeline:
          1. Parse the flat sitemap (via Playwright) to obtain article candidates.
          2. Filter by reaction keywords on the title (fast, no additional crawl).
          3. Crawl matching article pages for body text.
        """
        candidates = await self._collect_candidates()
        logger.info(
            "[%s] %d articles discovered in sitemap; applying keyword filter…",
            self.source_name, len(candidates),
        )

        relevant = [
            c for c in candidates
            if _contains_keyword(c["title"])
        ]
        logger.info(
            "[%s] %d articles passed keyword filter.", self.source_name, len(relevant)
        )

        if not relevant:
            return []

        return await self._crawl_articles(relevant)

    # ------------------------------------------------------------------
    # Sitemap discovery (Playwright-based)
    # ------------------------------------------------------------------

    async def _collect_candidates(self) -> list[dict]:
        """
        Fetch the flat Google News sitemap via Crawl4AI/Playwright and return
        a list of article candidate dicts:
            { url, title, published_at }

        The sitemap is protected by Cloudflare and returns 403 to plain HTTP
        requests.  Playwright bypasses the challenge.  Cloudflare's XSLT
        transformer converts the XML to an HTML table before the browser renders
        it; each row maps to one article:
            <tr>
              <td><a href="{article_url}">{title}</a></td>
              <td>{published_at}</td>
            </tr>

        Note: ``news:keywords`` is absent from the XSLT output — keyword
        pre-filtering therefore runs on article titles only.
        """
        sitemap_rc = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            page_timeout=30_000,
            wait_until="domcontentloaded",
            word_count_threshold=1,   # do not skip sparse pages (XML data)
        )

        async with AsyncWebCrawler(config=self._browser_config()) as crawler:
            result = await crawler.arun(url=_SITEMAP_URL, config=sitemap_rc)

        if not result.success:
            logger.error(
                "[%s] Failed to fetch sitemap: %s",
                self.source_name, result.error_message,
            )
            return []

        return self._parse_sitemap_html(result.html)

    def _parse_sitemap_html(self, html: str) -> list[dict]:
        """
        Parse the XSLT-rendered HTML of the sitemap and return candidate dicts.

        Expected table structure (per row):
          cell[0]: <a href="{article_url}">{title}</a>
          cell[1]: {published_at}  (ISO 8601 string)
        """
        soup = BeautifulSoup(html, "lxml")
        candidates: list[dict] = []
        seen_urls: set[str] = set()

        for a in soup.find_all("a", href=True):
            url = a["href"].strip()
            if not url or url in seen_urls:
                continue
            # Only include article URLs from eleftherostypos.gr
            if "eleftherostypos.gr" not in url:
                continue
            seen_urls.add(url)

            title = _clean_text(a.get_text(strip=True))

            # Publication date lives in the second <td> of the same <tr>
            published_at: str | None = None
            tr = a.find_parent("tr")
            if tr:
                cells = tr.find_all("td")
                if len(cells) >= 2:
                    date_str = cells[1].get_text(strip=True)
                    if date_str:
                        try:
                            published_at = datetime.fromisoformat(date_str).isoformat()
                        except ValueError:
                            published_at = date_str

            candidates.append({
                "url":          url,
                "title":        title,
                "published_at": published_at,
            })

        logger.info(
            "[%s] Parsed %d article candidates from sitemap HTML.",
            self.source_name, len(candidates),
        )
        return candidates

    # ------------------------------------------------------------------
    # Article page crawling
    # ------------------------------------------------------------------

    async def _crawl_articles(self, candidates: list[dict]) -> list[dict]:
        """
        Use Crawl4AI to fetch each candidate article URL and extract body text.
        Applies a polite delay between requests.
        """
        records: list[dict] = []
        scraped_at = datetime.now(timezone.utc).isoformat()

        async with AsyncWebCrawler(config=self._browser_config()) as crawler:
            for i, candidate in enumerate(candidates):
                if i > 0:
                    await asyncio.sleep(REQUEST_DELAY_SECONDS)

                url = candidate["url"]
                logger.info("[%s] Crawling article: %s", self.source_name, url)
                try:
                    result = await crawler.arun(url=url, config=self._run_config())
                    if result.success:
                        record = self._build_record(candidate, result, scraped_at)
                        records.append(record)
                    else:
                        logger.warning(
                            "[%s] Failed to crawl %s: %s",
                            self.source_name, url, result.error_message,
                        )
                except Exception as exc:
                    logger.error(
                        "[%s] Exception crawling %s: %s",
                        self.source_name, url, exc, exc_info=True,
                    )

        return records

    def _extract_article_body(self, result: CrawlResult) -> str:
        """
        Extract clean article body text from the crawled page HTML.

        eleftherostypos.gr page structure (confirmed via Playwright render):

        Standfirst   : h2.ap-title          (deck/subheading above body;
                                             lives outside div.ap-article-text)
        Body wrapper : div.ap-article-text  (contains all article paragraphs)
        Content kept : p                    (bare paragraphs with no class)

        Noise removed before text collection:
          div.adslot               — ad banner blocks (mobile + sticky)
          div.related-posts-by-tag — «ΔΙΑΒΑΣΤΕ ΕΠΙΣΗΣ» inline related-posts
          glomex-integration       — embedded video player widget
          script / style / iframe / noscript / figure

        Note: Section headings within the article body appear as plain <p>
        elements (short text, no heading tag or class), so they are collected
        alongside regular paragraphs without special treatment.
        """
        html = result.html
        if not html:
            return _clean_text(result.markdown or "")

        soup = BeautifulSoup(html, "lxml")

        # -- 1. Extract standfirst / subheading --------------------------------
        standfirst = ""
        standfirst_el = soup.select_one("h2.ap-title")
        if standfirst_el:
            standfirst = _clean_text(standfirst_el.get_text(strip=True))

        # -- 2. Locate the article body container -----------------------------
        body_el = soup.select_one("div.ap-article-text")
        if body_el is None:
            return _clean_text(result.markdown or "")

        # -- 3. Remove noise elements in-place --------------------------------
        _NOISE_SELECTORS = [
            "div.adslot",               # ad banner blocks (all variants)
            "div.related-posts-by-tag", # «ΔΙΑΒΑΣΤΕ ΕΠΙΣΗΣ» inline related posts
            "glomex-integration",       # embedded video player widget
            "script",
            "style",
            "iframe",
            "noscript",
            "figure",
        ]
        for sel in _NOISE_SELECTORS:
            for el in body_el.select(sel):
                el.decompose()

        # -- 4. Collect text from p elements -----------------------------------
        parts: list[str] = []
        for el in body_el.find_all("p"):
            txt = el.get_text(" ", strip=True)
            if txt:
                parts.append(txt)

        # -- 5. Deduplicate consecutive identical blocks -----------------------
        deduped: list[str] = []
        for part in parts:
            if not deduped or part != deduped[-1]:
                deduped.append(part)

        body = "\n\n".join(deduped).strip()
        if standfirst and not body.startswith(standfirst):
            body = standfirst + "\n\n" + body
        return body

    def _build_record(
        self,
        candidate: dict,
        result: CrawlResult,
        scraped_at: str,
    ) -> dict:
        """Assemble the final output record from sitemap metadata + crawled content."""
        return {
            "source":        self.source_name,
            "url":           candidate["url"],
            "title":         candidate["title"],
            "body":          self._extract_article_body(result),
            "published_at":  candidate["published_at"],
            "scraped_at":    scraped_at,
            "lang":          "el",
            "category_hint": None,
        }

