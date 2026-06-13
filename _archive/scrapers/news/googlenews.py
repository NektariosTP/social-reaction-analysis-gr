"""
scrapers/news/googlenews.py

Spider that queries Google News RSS feeds — one query per REACTION_KEYWORD —
to discover Greek news articles from any source indexed by Google.

Crawl strategy:
  1. For each keyword in REACTION_KEYWORDS, build a Google News RSS search URL
     with Greek locale parameters (hl=el, gl=GR, ceid=GR:el).  Multi-word
     keywords are wrapped in double-quotes for phrase matching.
  2. Fetch the RSS feed via httpx and parse article candidates (url, title,
     published_at).  At most _MAX_ARTICLES_PER_KEYWORD entries are kept per
     keyword to prevent runaway crawls for broad terms.
  3. Deduplicate article URLs across all keyword queries — the same article
     may match multiple keywords and should only be crawled once.
  4. For each unique candidate, fetch the article HTML:
       Primary  — httpx GET (fast, low overhead, handles most Greek sites).
       Fallback — Crawl4AI/Playwright (for JS-rendered or CF-protected pages).
  5. Extract body text with trafilatura.extract() — site-agnostic boilerplate
     removal applicable to any news layout.
  6. Apply the project's reaction-keyword filter as a secondary confirmation
     gate (Google pre-filtering is accurate but not perfect).

Rate limiting:
  REQUEST_DELAY_SECONDS is applied between successive RSS fetches and between
  successive article fetches.  A shorter _DECODE_DELAY_SECONDS is applied
  between successive Google News URL decode calls (which make 2 requests to
  Google per URL: one GET for sig/ts, one POST to batchexecute).

URL decoding:
  Google News RSS returns opaque redirect URLs of the form
  https://news.google.com/rss/articles/{base64_token}?oc=5.  Following these
  redirects via plain HTTP leads to Google's GDPR consent page in the EU/GR
  region.  The googlenewsdecoder library (new_decoderv1) resolves each token
  to the canonical article URL by calling Google's internal batchexecute API.
  The decode call is synchronous (uses requests internally) and is dispatched
  to a thread pool via asyncio.to_thread() to avoid blocking the event loop.

Note:
  Google News RSS is a public but undocumented endpoint.  The URL format
  (https://news.google.com/rss/search?q=...&hl=el&gl=GR&ceid=GR:el) was
  stable as of March 2026 but may change without notice.
"""

from __future__ import annotations

import asyncio
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote

import httpx
import trafilatura
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from googlenewsdecoder import new_decoderv1

from scrapers.news.base_news_spider import BaseNewsSpider, _contains_keyword, _clean_text
from scrapers.config import REACTION_KEYWORDS, REQUEST_DELAY_SECONDS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_GOOGLE_NEWS_RSS_TEMPLATE = (
    "https://news.google.com/rss/search?q={query}&hl=el&gl=GR&ceid=GR:el"
)

# Maximum articles to keep per keyword query (applied before deduplication).
# Raised from 10 → 30 now that this is the sole broad-coverage scraper.
_MAX_ARTICLES_PER_KEYWORD: int = 15

# Minimum body length (chars) for trafilatura output to be considered usable.
_MIN_BODY_LENGTH: int = 50

# Polite delay (seconds) between successive Google News URL decode calls.
# Each decode call makes 2 requests to Google (GET + POST); a short delay
# reduces the risk of rate limiting without significantly increasing total
# crawl time.
_DECODE_DELAY_SECONDS: float = 0.5

_RSS_HEADERS: dict[str, str] = {
    "User-Agent": "SocialReactionAnalysisBot/1.0",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

_ARTICLE_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*",
    "Accept-Language": "el-GR,el;q=0.9,en;q=0.8",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _encode_keyword(keyword: str) -> str:
    """
    URL-encode a keyword for the Google News RSS query parameter.
    Multi-word keywords are wrapped in double-quotes for phrase matching.
    """
    if " " in keyword:
        return quote(f'"{keyword}"')
    return quote(keyword)


async def _decode_google_news_url(google_url: str) -> str | None:
    """
    Resolve a Google News redirect URL to the canonical article URL.

    Google News RSS items (as of 2024+) return opaque redirect URLs of the
    form https://news.google.com/rss/articles/{base64_token}?oc=5.  Following
    these redirects via plain HTTP leads to Google's GDPR consent page in the
    GR/EU region instead of the actual article.

    This function dispatches ``new_decoderv1`` (synchronous, uses the
    ``googlenewsdecoder`` library) to a thread pool via asyncio.to_thread()
    to avoid blocking the asyncio event loop.

    Returns the resolved canonical URL string, or None if decoding fails.
    """
    try:
        result = await asyncio.to_thread(new_decoderv1, google_url)
        if result.get("status"):
            return result["decoded_url"]
        logger.debug(
            "[googlenews] URL decode failed for %s: %s",
            google_url, result.get("message"),
        )
        return None
    except Exception as exc:
        logger.debug("[googlenews] URL decode exception for %s: %s", google_url, exc)
        return None


def _strip_source_suffix(title: str, source_name: str) -> str:
    """
    Google News RSS titles carry a trailing `` - Source Name`` suffix.
    Strip it when the suffix matches the <source> element text.
    """
    suffix = f" - {source_name}"
    if title.endswith(suffix):
        return title[: -len(suffix)].strip()
    return title


def _parse_rfc2822(raw: str) -> str | None:
    """Convert an RFC 2822 date string to ISO 8601, or return the raw string on failure."""
    try:
        return parsedate_to_datetime(raw).isoformat()
    except Exception:
        return raw or None


# ---------------------------------------------------------------------------
# Spider
# ---------------------------------------------------------------------------

class GoogleNewsRSSScraper(BaseNewsSpider):
    """
    Scraper that queries Google News RSS feeds per REACTION_KEYWORD.

    Unlike the site-specific spiders, this scraper discovers articles from
    *any* Greek news source indexed by Google — broadening coverage beyond
    the fixed sources configured in config.py.

    The crawl is keyword-driven rather than site-driven:
      • One RSS query per keyword in REACTION_KEYWORDS
      • Article body extraction via trafilatura (site-agnostic)
      • Playwright fallback for JS-heavy or Cloudflare-protected sources
    """

    @property
    def source_name(self) -> str:
        return "googlenews"

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
        Full pipeline:
          1. Query Google News RSS for each REACTION_KEYWORD.
          2. Deduplicate article URLs across keyword queries.
          3. Fetch HTML and extract body text (httpx → trafilatura;
             Playwright fallback on failure).
          4. Apply keyword filter as secondary confirmation gate.
          5. Return flat list of structured record dicts.
        """
        candidates = await self._collect_candidates()
        logger.info(
            "[%s] %d unique article candidates after deduplication.",
            self.source_name, len(candidates),
        )

        if not candidates:
            return []

        records = await self._crawl_articles(candidates)

        # Secondary keyword filter: remove records where the extracted body
        # and title together no longer contain a reaction keyword.
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
    # RSS candidate discovery
    # ------------------------------------------------------------------

    async def _collect_candidates(self) -> list[dict]:
        """
        Issue one Google News RSS query per REACTION_KEYWORD.
        Returns a deduplicated flat list of article candidate dicts with
        canonical (non-Google-redirect) article URLs:
            { url, title, published_at, _kw_source }

        Pipeline:
          1. Fetch RSS per keyword → list of Google News redirect URL candidates.
          2. Deduplicate by Google News URL.
          3. Decode each Google News URL to its canonical article URL via the
             googlenewsdecoder batchexecute API (polite delay between calls).
          4. Re-deduplicate by canonical URL (multiple Google URLs can point to
             the same article).
        """
        # -- Phase 1 & 2: RSS fetch + deduplicate by Google News URL ----------
        seen_google_urls: set[str] = set()
        google_candidates: list[dict] = []

        async with httpx.AsyncClient(headers=_RSS_HEADERS, timeout=15.0) as client:
            for i, keyword in enumerate(REACTION_KEYWORDS):
                if i > 0:
                    await asyncio.sleep(REQUEST_DELAY_SECONDS)

                rss_url = _GOOGLE_NEWS_RSS_TEMPLATE.format(
                    query=_encode_keyword(keyword)
                )
                logger.info(
                    "[%s] Fetching RSS for keyword: %r", self.source_name, keyword
                )
                entries = await self._fetch_rss_candidates(rss_url, keyword, client)

                new = 0
                for entry in entries[:_MAX_ARTICLES_PER_KEYWORD]:
                    if entry["url"] not in seen_google_urls:
                        seen_google_urls.add(entry["url"])
                        google_candidates.append(entry)
                        new += 1

                logger.info(
                    "[%s] Keyword %r → %d entries, %d new after dedup.",
                    self.source_name, keyword, len(entries), new,
                )

        logger.info(
            "[%s] Resolving %d Google News redirect URLs to canonical article URLs…",
            self.source_name, len(google_candidates),
        )

        # -- Phase 3 & 4: Decode URLs + re-deduplicate by canonical URL -------
        seen_canonical: set[str] = set()
        resolved: list[dict] = []

        for i, candidate in enumerate(google_candidates):
            if i > 0:
                await asyncio.sleep(_DECODE_DELAY_SECONDS)

            canonical = await _decode_google_news_url(candidate["url"])
            if canonical is None:
                logger.warning(
                    "[%s] Failed to decode Google News URL: %s",
                    self.source_name, candidate["url"],
                )
                continue
            if canonical in seen_canonical:
                continue
            seen_canonical.add(canonical)
            candidate["url"] = canonical
            resolved.append(candidate)

        logger.info(
            "[%s] %d unique canonical URLs resolved (of %d Google News candidates).",
            self.source_name, len(resolved), len(google_candidates),
        )
        return resolved

    async def _fetch_rss_candidates(
        self,
        rss_url: str,
        keyword: str,
        client: httpx.AsyncClient,
    ) -> list[dict]:
        """
        Fetch and parse one Google News RSS URL.
        Returns a list of candidate dicts:
            { url, title, published_at, _kw_source }
        """
        try:
            resp = await client.get(rss_url, follow_redirects=True)
            resp.raise_for_status()
        except Exception as exc:
            logger.warning(
                "[%s] RSS fetch failed for keyword %r: %s",
                self.source_name, keyword, exc,
            )
            return []

        try:
            root = ET.fromstring(resp.content)
        except ET.ParseError as exc:
            logger.warning(
                "[%s] RSS XML parse error for keyword %r: %s",
                self.source_name, keyword, exc,
            )
            return []

        channel = root.find("channel")
        if channel is None:
            return []

        candidates: list[dict] = []
        for item in channel.findall("item"):
            url = self._extract_item_url(item)
            if not url:
                continue

            source_el = item.find("source")
            source_name = (
                source_el.text.strip()
                if source_el is not None and source_el.text
                else ""
            )

            title_raw = (item.findtext("title") or "").strip()
            title = _strip_source_suffix(title_raw, source_name)

            pubdate_raw = (item.findtext("pubDate") or "").strip()
            published_at = _parse_rfc2822(pubdate_raw)

            candidates.append({
                "url":          url,
                "title":        _clean_text(title),
                "published_at": published_at,
                "_kw_source":   keyword,   # keyword that surfaced this article (debug)
            })

        return candidates

    @staticmethod
    def _extract_item_url(item: ET.Element) -> str:
        """
        Extract the Google News redirect URL from an RSS <item> element.

        As of 2024+, Google News RSS returns opaque redirect URLs in both
        <link> and <guid>.  The canonical article URL is resolved later by
        _decode_google_news_url() via the batchexecute API.

        If <link> is absent, <guid> is tried as a fallback.
        """
        link = (item.findtext("link") or "").strip()
        if link:
            return link

        guid_el = item.find("guid")
        if guid_el is not None and guid_el.text:
            return guid_el.text.strip()

        return ""

    # ------------------------------------------------------------------
    # Article fetching and body extraction
    # ------------------------------------------------------------------

    async def _crawl_articles(self, candidates: list[dict]) -> list[dict]:
        """
        For each candidate, fetch HTML and extract body text.
        Primary: httpx + trafilatura.
        Fallback: Crawl4AI/Playwright + trafilatura.
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
        Fetch the article HTML and extract readable body text.

        Strategy:
          1. httpx GET — fast, resolves redirects (including Google News
             redirect URLs) transparently via follow_redirects=True.
          2. trafilatura.extract() on the response HTML.
          3. If httpx fails or trafilatura yields insufficient text →
             Playwright fallback via Crawl4AI.
          4. trafilatura.extract() on the Playwright-rendered HTML.

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
                html,
                include_comments=False,
                include_tables=False,
                no_fallback=False,
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
                word_count_threshold=1,   # do not skip sparse pages
            )
            result = await playwright_crawler.arun(url=url, config=pw_config)
            if result.success and result.html:
                body = trafilatura.extract(
                    result.html,
                    include_comments=False,
                    include_tables=False,
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
        """Assemble the final output record from RSS metadata and extracted body."""
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

    # ------------------------------------------------------------------
    # Override: parse() is unused — this spider overrides crawl() entirely.
    # Declared to satisfy the abstract interface inherited from BaseScraper.
    # ------------------------------------------------------------------

    async def parse(self, result) -> list[dict]:  # pragma: no cover
        return []
