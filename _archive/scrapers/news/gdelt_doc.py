"""
scrapers/news/gdelt_doc.py

Spider that queries the GDELT 2.0 Document API (DOC API v2) to discover
Greek social-reaction news articles.

Crawl strategy:
  1. Build a single GDELT query combining:
       • A parenthesized OR clause of English protest / labor-action terms
         (GDELT's full-text index is English-script; Greek Unicode keywords are
         NOT indexed and reliably return empty results).
       • The ``sourcecountry:Greece`` filter — restricts results to news
         sources headquartered in Greece, ensuring Greek-language articles
         and eliminating international noise.
     The query takes the form:
       (strike OR protest OR boycott OR demonstration OR …) sourcecountry:Greece
     A single GET request is issued to the GDELT DOC API.
  2. Deduplicate article URLs from the JSON response.
  3. Fetch each article's HTML:
       Primary  — httpx GET + trafilatura body extraction.
       Fallback — Crawl4AI/Playwright + trafilatura (for CF-protected pages).
  4. Apply the project's Greek-NLP reaction-keyword filter as a secondary gate
     to confirm the article body contains one of the REACTION_KEYWORDS.

Why NOT use Greek keywords directly:
  The GDELT DOC API's full-text index does not support Greek-script Unicode
  terms.  Queries with Greek Unicode return {} (no results).  Using English
  protest vocabulary + "Greece" context is the recommended workaround.

Differences vs GoogleNewsRSSScraper:
  - Single compound query per run (no per-keyword requests).
  - No URL decoding needed (GDELT returns canonical article URLs directly).
  - GDELT covers international Greek-language media (diaspora press, ERT World)
    that may not appear in Google News.
  - GDELT response includes article metadata (seendate, tone score).

Rate limit:
  GDELT DOC API enforces one request every 5 seconds.  A single query per
  run stays well within this limit.  A 429 response triggers one 60-second
  retry before giving up.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

import httpx
import trafilatura
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

from scrapers.news.base_news_spider import BaseNewsSpider, _contains_keyword, _clean_text
from scrapers.config import REQUEST_DELAY_SECONDS, GDELT_TIMESPAN_MINUTES

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_GDELT_DOC_API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

_MIN_BODY_LENGTH: int = 50

_HTTP_HEADERS: dict[str, str] = {
    "User-Agent": "SocialReactionAnalysisBot/1.0",
    "Accept":     "application/json",
}

_ARTICLE_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml,*/*",
    "Accept-Language": "el-GR,el;q=0.9,en;q=0.8",
}


# ---------------------------------------------------------------------------
# Module-level constants: English protest vocabulary for GDELT query
# ---------------------------------------------------------------------------

# GDELT DOC API full-text index is English-script only.  These terms are the
# English equivalents / translations of the Greek REACTION_KEYWORDS used in
# the NLP secondary filter.
_GDELT_EN_PROTEST_TERMS: tuple[str, ...] = (
    "strike",
    "protest",
    "demonstration",
    "rally",
    "occupation",
    "blockade",
    "boycott",
    "walkout",
    "riot",
    "clashes",
    "hacktivism",
    "whistleblower",
    "tear gas",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_gdelt_query() -> str:
    """
    Build the GDELT DOC API query string:
      (term1 OR term2 OR …) sourcecountry:Greece

    The ``sourcecountry:Greece`` filter restricts GDELT results to news
    sources physically headquartered in Greece, ensuring we only fetch
    Greek-language articles.  The English protest terms match GDELT's
    full-text index (Greek Unicode keywords are NOT indexed).
    Multi-word terms are phrase-quoted.  The OR clause is wrapped in parens
    as required by the GDELT DOC API.
    """
    terms = [f'"{t}"' if " " in t else t for t in _GDELT_EN_PROTEST_TERMS]
    return "(" + " OR ".join(terms) + ") sourcecountry:Greece"


def _parse_gdelt_seendate(seendate: str) -> str | None:
    """Parse a GDELT seendate string (YYYYMMDDTHHMMSSz) to ISO 8601."""
    try:
        return (
            datetime.strptime(seendate, "%Y%m%dT%H%M%Sz")
            .replace(tzinfo=timezone.utc)
            .isoformat()
        )
    except ValueError:
        return seendate or None


# ---------------------------------------------------------------------------
# Spider
# ---------------------------------------------------------------------------

class GDELTDocScraper(BaseNewsSpider):
    """
    Scraper that queries the GDELT 2.0 DOC API for Greek-language news articles.

    Issues a single compound OR query across all REACTION_KEYWORDS per run,
    avoiding per-keyword API calls and staying within GDELT's rate limit.
    Canonical article URLs are returned directly — no redirect decoding needed.
    """

    @property
    def source_name(self) -> str:
        return "gdelt_doc"

    @property
    def seed_urls(self) -> list[str]:
        # Not used by this spider's crawl() override.
        return []

    # ------------------------------------------------------------------
    # Public entry-point (overrides BaseScraper.crawl)
    # ------------------------------------------------------------------

    async def crawl(self) -> list[dict]:
        """
        Full pipeline:
          1. Query GDELT DOC API with a compound OR query.
          2. Deduplicate article URLs.
          3. Fetch HTML and extract body text (httpx → trafilatura;
             Playwright fallback on failure).
          4. Apply keyword filter as secondary confirmation gate.
          5. Return flat list of structured record dicts.
        """
        candidates = await self._collect_candidates()
        logger.info(
            "[%s] %d article candidates from GDELT DOC API.",
            self.source_name, len(candidates),
        )

        if not candidates:
            return []

        records = await self._crawl_articles(candidates)

        relevant = [
            r for r in records
            if _contains_keyword(r["title"] + " " + r["body"])
        ]
        logger.info(
            "[%s] %d records passed secondary keyword filter (of %d crawled).",
            self.source_name, len(relevant), len(records),
        )
        return relevant

    # ------------------------------------------------------------------
    # API discovery
    # ------------------------------------------------------------------

    async def _collect_candidates(self) -> list[dict]:
        """
        Issue a single GDELT DOC API request with a compound OR query.
        Returns a deduplicated list of candidate dicts:
            { url, title, published_at }
        """
        params = {
            "query":      _build_gdelt_query(),
            "mode":       "artlist",
            "format":     "json",
            "maxrecords": "75",
            "TIMESPAN":   str(GDELT_TIMESPAN_MINUTES),
        }

        async with httpx.AsyncClient(headers=_HTTP_HEADERS, timeout=20.0) as client:
            try:
                resp = await client.get(
                    _GDELT_DOC_API_URL,
                    params=params,
                    follow_redirects=True,
                )
                if resp.status_code == 429:
                    logger.warning(
                        "[%s] GDELT DOC API rate limit hit (429). "
                        "Retrying after 60 seconds…",
                        self.source_name,
                    )
                    await asyncio.sleep(60)
                    resp = await client.get(
                        _GDELT_DOC_API_URL,
                        params=params,
                        follow_redirects=True,
                    )
                resp.raise_for_status()
                body = resp.text.strip()
                if not body or body == "{}":
                    logger.warning(
                        "[%s] GDELT DOC API returned an empty response.",
                        self.source_name,
                    )
                    return []
                data = resp.json()
            except Exception as exc:
                logger.error(
                    "[%s] GDELT DOC API request failed: %s",
                    self.source_name, exc,
                )
                return []

        articles = data.get("articles") or []
        if not articles:
            logger.warning(
                "[%s] GDELT DOC API returned no articles for the current query.",
                self.source_name,
            )
            return []

        seen_urls: set[str] = set()
        candidates: list[dict] = []
        for article in articles:
            url = (article.get("url") or "").strip()
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            candidates.append({
                "url":          url,
                "title":        _clean_text(article.get("title") or ""),
                "published_at": _parse_gdelt_seendate(article.get("seendate") or ""),
            })

        logger.info(
            "[%s] %d unique candidates parsed from GDELT API response.",
            self.source_name, len(candidates),
        )
        return candidates

    # ------------------------------------------------------------------
    # Article fetching and body extraction
    # ------------------------------------------------------------------

    async def _crawl_articles(self, candidates: list[dict]) -> list[dict]:
        """
        Fetch each article's HTML and extract body text.
        Primary: httpx + trafilatura. Fallback: Crawl4AI/Playwright.
        Applies REQUEST_DELAY_SECONDS between successive requests.
        """
        records: list[dict] = []
        scraped_at = datetime.now(timezone.utc).isoformat()

        async with httpx.AsyncClient(
            headers=_ARTICLE_HEADERS,
            timeout=20.0,
            follow_redirects=True,
        ) as http_client:
            async with AsyncWebCrawler(config=self._browser_config()) as playwright_crawler:
                for i, candidate in enumerate(candidates):
                    if i > 0:
                        await asyncio.sleep(REQUEST_DELAY_SECONDS)

                    url = candidate["url"]
                    logger.info("[%s] Fetching article: %s", self.source_name, url)

                    body = await self._fetch_and_extract(url, http_client, playwright_crawler)
                    if body is None:
                        logger.warning(
                            "[%s] Could not extract body for %s — skipping.",
                            self.source_name, url,
                        )
                        continue

                    records.append(self._build_record(candidate, body, scraped_at))

        return records

    async def _fetch_and_extract(
        self,
        url: str,
        http_client: httpx.AsyncClient,
        playwright_crawler: AsyncWebCrawler,
    ) -> str | None:
        """
        Fetch article HTML and extract readable body text via trafilatura.
        Falls back to Playwright if httpx fails or body is insufficient.
        Returns the extracted body string, or None if all strategies fail.
        """
        # -- Primary: httpx ---------------------------------------------------
        html: str | None = None
        try:
            resp = await http_client.get(url)
            if resp.status_code == 200:
                html = resp.text
        except Exception as exc:
            logger.debug("[%s] httpx failed for %s: %s", self.source_name, url, exc)

        if html:
            body = trafilatura.extract(
                html, include_comments=False, include_tables=False, no_fallback=False,
            )
            if body and len(body.strip()) >= _MIN_BODY_LENGTH:
                return _clean_text(body)

        # -- Fallback: Playwright via Crawl4AI --------------------------------
        logger.debug(
            "[%s] httpx/trafilatura insufficient for %s — using Playwright fallback.",
            self.source_name, url,
        )
        try:
            pw_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                page_timeout=30_000,
                wait_until="domcontentloaded",
                word_count_threshold=1,
            )
            result = await playwright_crawler.arun(url=url, config=pw_config)
            if result.success and result.html:
                body = trafilatura.extract(
                    result.html, include_comments=False, include_tables=False,
                    no_fallback=False,
                )
                if body and len(body.strip()) >= _MIN_BODY_LENGTH:
                    return _clean_text(body)
        except Exception as exc:
            logger.error(
                "[%s] Playwright fallback failed for %s: %s",
                self.source_name, url, exc, exc_info=True,
            )

        return None

    # ------------------------------------------------------------------
    # Record assembly
    # ------------------------------------------------------------------

    def _build_record(self, candidate: dict, body: str, scraped_at: str) -> dict:
        """Assemble the final output record from GDELT metadata and extracted body."""
        return {
            "source":        self.source_name,
            "url":           candidate["url"],
            "title":         candidate["title"],
            "body":          body,
            "published_at":  candidate["published_at"],
            "scraped_at":    scraped_at,
            "lang":          "el",
            "category_hint": None,
        }

    async def parse(self, result) -> list[dict]:  # pragma: no cover
        return []
