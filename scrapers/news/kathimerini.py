"""
scrapers/news/kathimerini.py

Spider for https://www.kathimerini.gr — Greek online news portal.

Crawl strategy — RSS-driven:
  1. Fetch the RSS feed at the configured ``rss_url``.
  2. Parse each <item>: title, link, pubDate, media:keywords, description.
  3. Apply the reaction-keyword filter on title + keywords + description
     *before* hitting any article URLs — pre-crawl filtering is possible
     here because the RSS feed exposes full titles and keyword metadata.
  4. Crawl only the matching article pages with Crawl4AI to retrieve body text.

Note on coverage:
  The RSS feed is a rolling snapshot of recent articles (typically ~100 items).
  It does not provide historical pagination. For a scheduler that runs every
  hour this coverage window is sufficient.

Note on body-text quality:
  Article body text extraction is site-specific and will be implemented once
  the HTML structure has been mapped. A fallback to Crawl4AI's markdown output
  is provided in the interim.
"""

from __future__ import annotations

import asyncio
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import httpx
from crawl4ai import AsyncWebCrawler, CrawlResult

from scrapers.news.base_news_spider import BaseNewsSpider, _contains_keyword, _clean_text
from scrapers.config import NEWS_SOURCES, REQUEST_DELAY_SECONDS

logger = logging.getLogger(__name__)

_SOURCE_CFG = next(s for s in NEWS_SOURCES if s["name"] == "kathimerini")

# ---------------------------------------------------------------------------
# XML namespaces used by the Kathimerini RSS feed
# ---------------------------------------------------------------------------

_NS: dict[str, str] = {
    "atom":  "http://www.w3.org/2005/Atom",
    "dc":    "http://purl.org/dc/elements/1.1/",
    "media": "http://search.yahoo.com/mrss/",
}

_RSS_URL: str = _SOURCE_CFG["rss_url"]

_HTTP_HEADERS: dict[str, str] = {
    "User-Agent": "SocialReactionAnalysisBot/1.0",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}


# ---------------------------------------------------------------------------
# Low-level XML helpers
# ---------------------------------------------------------------------------

def _elem_text(el: ET.Element, tag: str, ns: dict[str, str] | None = None) -> str:
    """Return stripped text of the first child matching *tag*, or ''."""
    child = el.find(tag, ns) if ns else el.find(tag)
    return child.text.strip() if child is not None and child.text else ""


async def _fetch_xml(url: str, client: httpx.AsyncClient) -> ET.Element | None:
    """GET *url* and parse the response body as XML.  Returns None on any failure."""
    try:
        resp = await client.get(url, follow_redirects=True, timeout=15.0)
        resp.raise_for_status()
        return ET.fromstring(resp.content)
    except Exception as exc:
        logger.warning("[kathimerini] Failed to fetch XML from %s: %s", url, exc)
        return None


def _parse_rfc2822(raw: str) -> str | None:
    """Convert an RFC 2822 date string to ISO 8601, or return the raw string on failure."""
    try:
        return parsedate_to_datetime(raw).isoformat()
    except Exception:
        return raw or None


# ---------------------------------------------------------------------------
# Spider
# ---------------------------------------------------------------------------

class KathimeriniScraper(BaseNewsSpider):
    """
    Scraper for kathimerini.gr — RSS-driven strategy.

    Overrides ``crawl()`` from BaseScraper to implement a multi-step
    discovery process via the site's RSS feed instead of crawling
    category listing pages.

    The RSS feed exposes article titles, summaries, and keywords, enabling
    keyword pre-filtering *before* any article pages are crawled.
    """

    @property
    def source_name(self) -> str:
        return "kathimerini"

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
        Full RSS-driven crawl pipeline:
          1. Fetch the RSS feed and parse article candidates.
          2. Filter by reaction keywords on title + keywords + description (pre-crawl).
          3. Crawl matching article pages for body text.
        """
        candidates = await self._collect_candidates()
        logger.info(
            "[%s] %d articles discovered in RSS feed; applying keyword filter…",
            self.source_name, len(candidates),
        )

        relevant = [
            c for c in candidates
            if _contains_keyword(
                c["title"]
                + " " + c.get("_rss_keywords", "")
                + " " + c.get("_rss_description", "")
            )
        ]
        logger.info(
            "[%s] %d articles passed keyword filter.", self.source_name, len(relevant)
        )

        if not relevant:
            return []

        return await self._crawl_articles(relevant)

    # ------------------------------------------------------------------
    # RSS discovery
    # ------------------------------------------------------------------

    async def _collect_candidates(self) -> list[dict]:
        """
        Fetch the RSS feed and return a list of article candidate dicts:
            { url, title, published_at, _rss_keywords, _rss_description }
        """
        async with httpx.AsyncClient(headers=_HTTP_HEADERS) as client:
            root = await _fetch_xml(_RSS_URL, client)

        if root is None:
            logger.error("[%s] Failed to fetch RSS feed.", self.source_name)
            return []

        channel = root.find("channel")
        if channel is None:
            logger.error("[%s] No <channel> element found in RSS feed.", self.source_name)
            return []

        candidates: list[dict] = []
        seen_urls: set[str] = set()

        for item in channel.findall("item"):
            url = _elem_text(item, "link")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            title       = _elem_text(item, "title")
            pubdate_raw = _elem_text(item, "pubDate")
            kw_raw      = _elem_text(item, "media:keywords", _NS)
            desc_raw    = _elem_text(item, "description")

            candidates.append({
                "url":              url,
                "title":            title,
                "published_at":     _parse_rfc2822(pubdate_raw),
                "_rss_keywords":    kw_raw,    # temporary; stripped before final output
                "_rss_description": desc_raw,  # temporary; stripped before final output
            })

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

        Kathimerini.gr uses a WordPress-based layout.  The relevant selectors:
        - Lead/excerpt paragraph  : div.nx-excerpt          (above entry-content)
        - Body container          : div.entry-content        (WordPress standard)
        - Content elements kept   : p, h2, h3, h4, blockquote
        - Noise elements removed  : ad banners, subscription prompts, related-article
                                    embeds, author credits, social-share bars, TTS
                                    widget, article tags, inline figures.
        """
        from bs4 import BeautifulSoup

        html = result.html
        if not html:
            return _clean_text(result.markdown or "")

        soup = BeautifulSoup(html, "lxml")
        parts: list[str] = []

        # --- 1. Lead/excerpt paragraph (lives outside entry-content) ----------
        excerpt_el = soup.select_one("div.nx-excerpt")
        if excerpt_el:
            lead = excerpt_el.get_text(" ", strip=True)
            if lead:
                parts.append(lead)

        # --- 2. Main body container -------------------------------------------
        ec = soup.select_one("div.entry-content")
        if ec is None:
            return _clean_text(result.markdown or "")

        # Remove all known noise containers before text extraction
        _NOISE_SELECTORS = [
            "div.social-share-wrapper",
            "div.nx-banner-wrapper",
            "div.k-read-more-wrapper",
            "div.ka-newsletter-signup-div",
            "div.nx-credits-box",
            "div.nx-single-tags-wrapper",
            "div.entry-content-meta-wrapper",
            "div.text-to-speech-wrap",
            "figure",
            "script",
            "style",
            "iframe",
            "noscript",
        ]
        for sel in _NOISE_SELECTORS:
            for el in ec.select(sel):
                el.decompose()

        # Remove in-article subscription / newsletter prompts
        for el in ec.find_all("div", class_=lambda c: c and "p-inarticle" in c):
            el.decompose()

        # --- 3. Collect text from block-level content elements ----------------
        for el in ec.find_all(["p", "h2", "h3", "h4", "blockquote"]):
            txt = el.get_text(" ", strip=True)
            if txt:
                parts.append(txt)

        # --- 4. Deduplicate consecutive identical blocks ----------------------
        deduped: list[str] = []
        for p in parts:
            if not deduped or p != deduped[-1]:
                deduped.append(p)

        return "\n\n".join(deduped).strip()

    def _build_record(
        self,
        candidate: dict,
        result: CrawlResult,
        scraped_at: str,
    ) -> dict:
        """Assemble the final output record from RSS metadata + crawled content."""
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
