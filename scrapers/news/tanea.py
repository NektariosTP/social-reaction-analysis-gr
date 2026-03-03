"""
scrapers/news/tanea.py

Spider for https://www.tanea.gr — Greek online newspaper.

Crawl strategy — sitemap-driven (single flat sitemap):
  1. Fetch the single Google News sitemap at the configured ``sitemap_url``.
     Unlike protothema.gr, tanea.gr uses a flat <urlset> file with no
     sitemap index level; all article entries are contained in one document.
  2. Parse each <url> entry: loc, news:title, news:publication_date,
     news:keywords.
  3. Apply the reaction-keyword filter on title + sitemap keywords
     *before* hitting any article URLs — avoids unnecessary browser crawls.
  4. Crawl only the matching article pages with Crawl4AI to retrieve body text.

Note on body-text extraction:
  Site-specific HTML extraction has not yet been implemented.The current
  implementation falls back to Crawl4AI's auto-generated markdown output.
  Override ``_extract_article_body`` in a follow-up session once the
  tanea.gr page structure has been mapped.
"""

from __future__ import annotations

import asyncio
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import httpx
from crawl4ai import AsyncWebCrawler, CrawlResult

from scrapers.news.base_news_spider import BaseNewsSpider, _contains_keyword, _clean_text
from scrapers.config import NEWS_SOURCES, REQUEST_DELAY_SECONDS

logger = logging.getLogger(__name__)

_SOURCE_CFG = next(s for s in NEWS_SOURCES if s["name"] == "tanea")

# ---------------------------------------------------------------------------
# XML namespace map for tanea.gr's Google News sitemap
# ---------------------------------------------------------------------------

_NS: dict[str, str] = {
    "sm":    "http://www.sitemaps.org/schemas/sitemap/0.9",
    "news":  "http://www.google.com/schemas/sitemap-news/0.9",
    "image": "http://www.google.com/schemas/sitemap-image/1.1",
}

_SITEMAP_URL: str = _SOURCE_CFG["sitemap_url"]

_HTTP_HEADERS: dict[str, str] = {
    "User-Agent": "SocialReactionAnalysisBot/1.0",
    "Accept": "application/xml, text/xml, */*",
}


# ---------------------------------------------------------------------------
# Low-level XML helpers
# ---------------------------------------------------------------------------

def _xml_text(el: ET.Element, path: str) -> str:
    """Return stripped text of the first descendant matching *path*, or ''."""
    node = el.find(path, _NS)
    return node.text.strip() if node is not None and node.text else ""


async def _fetch_xml(url: str, client: httpx.AsyncClient) -> ET.Element | None:
    """GET *url* and parse the response body as XML.  Returns None on any failure."""
    try:
        resp = await client.get(url, follow_redirects=True, timeout=15.0)
        resp.raise_for_status()
        return ET.fromstring(resp.content)
    except Exception as exc:
        logger.warning("[tanea] Failed to fetch XML from %s: %s", url, exc)
        return None


# ---------------------------------------------------------------------------
# Spider
# ---------------------------------------------------------------------------

class TaneaScraper(BaseNewsSpider):
    """
    Scraper for tanea.gr — single flat sitemap-driven strategy.

    Overrides ``crawl()`` from BaseScraper to implement a two-step pipeline:
      1. Fetch the flat Google News sitemap and extract article candidates.
      2. Apply the reaction-keyword filter on title + sitemap keywords.
      3. Crawl matching article pages for body text via Crawl4AI.

    Unlike protothema.gr (which uses a sitemap index with multiple child
    sitemaps), tanea.gr publishes all recent articles in a single <urlset>
    document, so no index-level fetching is needed.
    """

    @property
    def source_name(self) -> str:
        return "tanea"

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
          1. Parse the flat sitemap to obtain article candidates.
          2. Filter by reaction keywords (fast, no browser).
          3. Crawl matching article pages for body text.
        """
        candidates = await self._collect_candidates()
        logger.info(
            "[%s] %d articles discovered in sitemap; applying keyword filter…",
            self.source_name, len(candidates),
        )

        relevant = [
            c for c in candidates
            if _contains_keyword(c["title"] + " " + c.get("_sitemap_keywords", ""))
        ]
        logger.info(
            "[%s] %d articles passed keyword filter.", self.source_name, len(relevant)
        )

        if not relevant:
            return []

        return await self._crawl_articles(relevant)

    # ------------------------------------------------------------------
    # Sitemap discovery
    # ------------------------------------------------------------------

    async def _collect_candidates(self) -> list[dict]:
        """
        Fetch the flat Google News sitemap and return a list of article
        candidate dicts:
            { url, title, published_at, _sitemap_keywords }
        """
        async with httpx.AsyncClient(headers=_HTTP_HEADERS) as client:
            root = await _fetch_xml(_SITEMAP_URL, client)

        if root is None:
            logger.error("[%s] Failed to fetch sitemap.", self.source_name)
            return []

        candidates: list[dict] = []
        seen_urls: set[str] = set()

        for url_el in root.findall("sm:url", _NS):
            loc = _xml_text(url_el, "sm:loc")
            if not loc or loc in seen_urls:
                continue
            seen_urls.add(loc)

            news_el = url_el.find("news:news", _NS)
            title         = _xml_text(news_el, "news:title")           if news_el is not None else ""
            published_raw = _xml_text(news_el, "news:publication_date") if news_el is not None else ""
            kw_raw        = _xml_text(news_el, "news:keywords")        if news_el is not None else ""

            published_at: str | None = None
            if published_raw:
                try:
                    published_at = datetime.fromisoformat(published_raw).isoformat()
                except ValueError:
                    published_at = published_raw

            candidates.append({
                "url":               loc,
                "title":             title,
                "published_at":      published_at,
                "_sitemap_keywords": kw_raw,   # temporary; stripped before final output
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

        tanea.gr page structure (confirmed across article types and /print/ variants):

        Subheading   : h2.post-summary  (prepended to body text)
        Body wrapper : div.post-body    (also carries main-content, article-wrapper classes)

        Content elements collected (in document order):
          p           — article paragraphs (no class on content paragraphs)
          h2          — in-article section headings (e.g. class='', 'inline-header')
          h3          — in-article section sub-headings (injected by JS renderer;
                        absent from server-side HTML, present in Playwright output)
          ul (bare)   — live-blog / highlights bullet list; <li> items formatted as «- »
          div.x_elementToProof — email-client-style quote block; text in <a>/<strong>,
                                  NOT wrapped in <p>, so collected directly.

        Noise removed before collection:
          div.is-hidden-touch         — desktop ad banner wrappers
          div.is-hidden-desktop       — mobile ad banner wrappers
          div.wrap_article_banner     — ad banner wrappers
          div.aem__gem_comments       — comments section
          div.wrap___headlines        — "latest news" headlines widget
          div.wrap-das-text           — additional ad wrappers
          ul.dailyHeadlines_list      — "latest news" list widget
          script / style / iframe / noscript / figure

        A single document-order traversal with a ``seen_ids`` guard prevents
        double-counting descendants of <ul> and div.x_elementToProof blocks.
        """
        from bs4 import BeautifulSoup

        html = result.html
        if not html:
            return _clean_text(result.markdown or "")

        soup = BeautifulSoup(html, "lxml")

        # -- 1. Extract standfirst / subheading --------------------------------
        standfirst = ""
        standfirst_el = soup.select_one("h2.post-summary")
        if standfirst_el:
            standfirst = _clean_text(standfirst_el.get_text(strip=True))

        # -- 2. Locate the article body container -----------------------------
        body_el = soup.select_one("div.post-body")
        if body_el is None:
            return _clean_text(result.markdown or "")

        # -- 3. Remove noise elements in-place --------------------------------
        _NOISE_SELECTORS = [
            "div.is-hidden-touch",       # desktop ad banner wrappers
            "div.is-hidden-desktop",     # mobile ad banner wrappers
            "div.wrap_article_banner",   # generic ad banner wrappers
            "div.aem__gem_comments",     # comments section
            "div.wrap___headlines",      # "latest news" headlines widget
            "div.wrap-das-text",         # additional ad wrappers
            "ul.dailyHeadlines_list",    # "latest news" list widget
            "script",
            "style",
            "iframe",
            "noscript",
            "figure",
        ]
        for sel in _NOISE_SELECTORS:
            for el in body_el.select(sel):
                el.decompose()

        # -- 4. Collect content in document order ------------------------------
        # ``seen_ids`` prevents double-counting descendants of composite blocks
        # (ul, div.x_elementToProof) when the traversal later reaches them.
        parts: list[str] = []
        seen_ids: set[int] = set()

        for el in body_el.find_all(True):
            eid = id(el)
            if eid in seen_ids:
                continue

            tag = el.name
            cls_set = set(el.get("class", []))

            if tag in ("p", "h2", "h3"):
                txt = el.get_text(" ", strip=True)
                if txt:
                    parts.append(txt)

            elif tag == "ul":
                # Mark all descendants as seen so their <li>/<p> are not re-visited.
                for desc in el.find_all(True):
                    seen_ids.add(id(desc))
                items = [
                    li.get_text(" ", strip=True)
                    for li in el.find_all("li")
                    if li.get_text(strip=True)
                ]
                if items:
                    parts.append("\n".join(f"- {item}" for item in items))

            elif tag == "div" and "x_elementToProof" in cls_set:
                # Bare-text quote block: content is in <a>/<strong>, not <p>.
                for desc in el.find_all(True):
                    seen_ids.add(id(desc))
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
