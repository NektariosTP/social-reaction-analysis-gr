"""
scrapers/news/protothema.py

Spider for https://www.protothema.gr — Greek online news portal.

Crawl strategy — sitemap-driven:
  1. Fetch the NewsArticles sitemap index to obtain individual sitemap file URLs.
  2. Parse the most recent ``sitemap_pages`` sitemap XMLs (each file covers a
     short time window and lists ~200 to ~400 articles with title, publication date, and
     keywords already in structured form).
  3. Apply the reaction-keyword filter on the title + sitemap keywords fields
     *before* hitting any article URLs — this avoids unnecessary browser crawls.
  4. Crawl only the matching article pages with Crawl4AI to retrieve body text.

Note on body-text quality:
  Article body text is extracted from ``div.articleContainer__main > div.cnt``
  using BeautifulSoup.  The text lives in bare text nodes separated by ``<br>``
  tags (no ``<p>`` wrappers).  Known noise elements (ad banners, scripts,
  related-article blocks) are removed before text collection.  Additional noise
  patterns can be added to the ``_NOISE_SELECTORS`` / ``_RELATED_SELECTORS``
  tuples in ``_extract_article_body`` as they are discovered during validation.
"""

from __future__ import annotations

import asyncio
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import httpx
from crawl4ai import AsyncWebCrawler, CrawlResult

from scrapers.news.base_news_spider import BaseNewsSpider, _contains_keyword, _clean_text
from scrapers.config import NEWS_SOURCES, REQUEST_DELAY_SECONDS

logger = logging.getLogger(__name__)

_SOURCE_CFG = next(s for s in NEWS_SOURCES if s["name"] == "protothema")

# ---------------------------------------------------------------------------
# XML namespace map for Protothema's Google News sitemaps
# ---------------------------------------------------------------------------

_NS: dict[str, str] = {
    "sm":    "http://www.sitemaps.org/schemas/sitemap/0.9",
    "news":  "http://www.google.com/schemas/sitemap-news/0.9",
    "image": "http://www.google.com/schemas/sitemap-image/1.1",
}

_SITEMAP_INDEX_URL: str = _SOURCE_CFG["sitemap_index_url"]
_SITEMAP_PAGES: int = _SOURCE_CFG.get("sitemap_pages", 3)

_HTTP_HEADERS: dict[str, str] = {
    "User-Agent": "SocialReactionAnalysisBot/1.0 (+https://github.com/your-org/social-reaction-analysis-gr)",
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
        logger.warning("[protothema] Failed to fetch XML from %s: %s", url, exc)
        return None


# ---------------------------------------------------------------------------
# Spider
# ---------------------------------------------------------------------------

class ProtothemaScraper(BaseNewsSpider):
    """
    Scraper for protothema.gr — sitemap-driven strategy.

    Overrides ``crawl()`` from BaseScraper to implement a multi-step
    discovery process via the Google News sitemap instead of crawling
    category listing pages.
    """

    @property
    def source_name(self) -> str:
        return "protothema"

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
          1. Resolve article candidates from the sitemap.
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
        Fetch the sitemap index and the most-recent ``_SITEMAP_PAGES`` individual
        sitemap files.  Returns a flat list of article candidate dicts:
            { url, title, published_at, _sitemap_keywords }
        """
        async with httpx.AsyncClient(headers=_HTTP_HEADERS) as client:
            sitemap_urls = await self._get_sitemap_urls(client)
            if not sitemap_urls:
                logger.error("[%s] No sitemap URLs found in index.", self.source_name)
                return []

            # The index lists sitemaps newest-first; take the first N for recency.
            target_sitemaps = sitemap_urls[:_SITEMAP_PAGES]

            candidates: list[dict] = []
            seen_urls: set[str] = set()
            for i, sm_url in enumerate(target_sitemaps):
                if i > 0:
                    await asyncio.sleep(REQUEST_DELAY_SECONDS)
                entries = await self._parse_news_sitemap(sm_url, client)
                for entry in entries:
                    if entry["url"] not in seen_urls:
                        seen_urls.add(entry["url"])
                        candidates.append(entry)

        return candidates

    async def _get_sitemap_urls(self, client: httpx.AsyncClient) -> list[str]:
        """Parse the sitemap index and return contained sitemap <loc> URLs."""
        root = await _fetch_xml(_SITEMAP_INDEX_URL, client)
        if root is None:
            return []
        return [_xml_text(sm, "sm:loc") for sm in root.findall("sm:sitemap", _NS)]

    async def _parse_news_sitemap(
        self, sitemap_url: str, client: httpx.AsyncClient
    ) -> list[dict]:
        """
        Parse an individual NewsArticles sitemap XML.
        Extracts per-article: url, title, published_at (ISO 8601), sitemap keywords.
        """
        root = await _fetch_xml(sitemap_url, client)
        if root is None:
            return []

        entries: list[dict] = []
        for url_el in root.findall("sm:url", _NS):
            loc = _xml_text(url_el, "sm:loc")
            if not loc:
                continue

            news_el = url_el.find("news:news", _NS)
            title          = _xml_text(news_el, "news:title")          if news_el is not None else ""
            published_raw  = _xml_text(news_el, "news:publication_date") if news_el is not None else ""
            kw_raw         = _xml_text(news_el, "news:keywords")       if news_el is not None else ""

            published_at: str | None = None
            if published_raw:
                try:
                    published_at = datetime.fromisoformat(published_raw).isoformat()
                except ValueError:
                    # Keep the raw string if it cannot be parsed.
                    published_at = published_raw

            entries.append({
                "url":               loc,
                "title":             title,
                "published_at":      published_at,
                "_sitemap_keywords": kw_raw,   # temporary; stripped before final output
            })

        return entries

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

        Protothema article pages have the body text inside one or more
        ``div.cnt`` elements that are direct children of
        ``div.articleContainer__main``.  These content blocks are sometimes
        separated by ad-banner ``div.cnt`` wrappers that contain no useful
        text.  Paragraphs are NOT wrapped in ``<p>`` tags — they are bare
        text nodes separated by ``<br>`` pairs.

        Strategy:
          1. Collect **all** ``div.cnt`` children inside
             ``div.articleContainer__main`` and concatenate their text
             (skipping ad-only containers).
          2. Remove noise elements in-place (ad banners, scripts, images,
             embedded Instagram posts, related-article blocks).
          3. Replace ``<br>`` tags with newlines, unwrap inline elements.
          4. Extract text, merge orphan keyword lines, and combine split
             embedded-tweet fragments.
          5. Fallback to Crawl4AI's markdown output if the container is absent.

        Note: Extend ``_NOISE_SELECTORS`` / ``_RELATED_SELECTORS`` as new
        noise patterns are discovered during validation.
        """
        from bs4 import BeautifulSoup, Tag

        raw_html = result.html
        if not raw_html:
            return _clean_text(result.markdown or "")

        soup = BeautifulSoup(raw_html, "lxml")

        # -- 0. Locate the article main wrapper --------------------------------
        main = soup.select_one("div.articleContainer__main")
        if main is None:
            return _clean_text(result.markdown or "")

        # Collect ALL div.cnt children (there may be several, separated by
        # ad-banner div.cnt blocks).  Skip containers that hold only ad
        # banners (no substantive text).
        cnt_blocks: list[Tag] = main.select(":scope > div.cnt")
        if not cnt_blocks:
            cnt_blocks = [main]   # fallback to the whole wrapper

        for container in cnt_blocks:
            # -- 1. Drop hard-coded noise elements -----------------------------
            _NOISE_SELECTORS = (
                "figure",           # images / captions
                "div.bannerWrp",    # ad banners (including stickyBanner variants)
                "div.bannerCnt",    # inner ad containers
                "div.banner-container",
                "script",
                "style",
                "iframe",           # embedded players / ads
                "noscript",
            )
            for sel in _NOISE_SELECTORS:
                for el in container.select(sel):
                    el.decompose()

            # -- 2. Drop Instagram embeds --------------------------------------
            # Instagram embed blocks appear as <blockquote class="instagram-media">
            # or elements whose text starts with known Instagram labels.
            for bq in container.select("blockquote.instagram-media"):
                bq.decompose()
            _INSTAGRAM_PREFIXES = (
                "View this post on Instagram",
                "Δείτε αυτή τη δημοσίευση στο Instagram",
                "Η δημοσίευση κοινοποιήθηκε από",
                "A post shared by",
            )
            for el in container.find_all(True):
                txt = el.get_text(strip=True)
                if any(txt.startswith(pfx) for pfx in _INSTAGRAM_PREFIXES):
                    el.decompose()
            # Also catch free-standing Instagram artifact text after extraction
            _INSTAGRAM_ARTIFACTS = _INSTAGRAM_PREFIXES

            # -- 3. Drop "Related Articles" blocks -----------------------------
            _RELATED_SELECTORS = (
                ".relatedArticles",
                ".related-articles",
                ".related_articles",
                '[class*="relatedArt"]',
                '[class*="RelatedArt"]',
            )
            for sel in _RELATED_SELECTORS:
                for el in container.select(sel):
                    el.decompose()

            _RELATED_LABELS = ("σχετικά άρθρα", "related articles")
            for el in container.find_all(True):
                label = el.get_text(strip=True).lower()
                if any(label.startswith(lbl) for lbl in _RELATED_LABELS):
                    el.decompose()

            # -- 4. Flatten embedded tweet blockquotes -------------------------
            # Each <blockquote class="twitter-tweet"> is a discrete unit that
            # should become a single line in the output.  Flatten its internal
            # HTML (which may contain <p> tags, links, etc.) into one text
            # string before the br→newline / inline-unwrap steps.
            for bq in container.select("blockquote.twitter-tweet"):
                tweet_text = re.sub(r"\s+", " ", bq.get_text(separator=" ")).strip()
                bq.clear()
                bq.string = tweet_text

            # -- 5. Normalise <br> → newline -----------------------------------
            for br in container.find_all("br"):
                br.replace_with("\n")

            # -- 6. Unwrap inline elements (strong-as-heading detection) -------
            _INLINE_TAGS = ("a", "em", "b", "i", "span")
            for tag_name in _INLINE_TAGS:
                for el in container.find_all(tag_name):
                    el.unwrap()
            # <strong> needs special handling: short text preceded by a
            # newline (or at container start) likely acts as a section
            # heading rather than inline emphasis.
            for el in container.find_all("strong"):
                text = el.get_text(strip=True)
                if not text:
                    el.decompose()
                    continue
                prev_text = str(el.previous_sibling) if el.previous_sibling else ""
                if len(text) < 60 and ("\n" in prev_text or not prev_text.strip()):
                    el.replace_with(text + "\n")
                else:
                    el.unwrap()

        # -- 7. Collect text from all content blocks ---------------------------
        all_lines: list[str] = []
        for container in cnt_blocks:
            raw_text = container.get_text(separator="\n")
            for line in raw_text.split("\n"):
                cleaned = re.sub(r"[ \t]+", " ", line).strip()
                if cleaned:
                    all_lines.append(cleaned)

        # Drop remaining Instagram artifact lines
        lines = [
            ln for ln in all_lines
            if not any(ln.startswith(art) for art in _INSTAGRAM_ARTIFACTS)
        ]

        # -- 8. Merge orphan keyword lines back into surrounding text ----------
        # Protothema wraps keywords in <a> tags flanked by <br><br> pairs.
        # After unwrap, these produce short orphan lines surrounded by
        # continuation text.  Rules:
        #   a) If the line starts with punctuation or lowercase → continuation.
        #   b) If the line is short (<60 chars), the prev line doesn't end
        #      with sentence-ending punctuation, AND the current line itself
        #      does NOT end with sentence punctuation → orphan keyword fragment.
        #      (Lines that form complete sentences, even short ones, are kept
        #      as separate paragraphs — this prevents headings from being
        #      swallowed.)
        #   c) If the prev line is long (>55 chars) and doesn't end with
        #      sentence punctuation → the sentence was likely split mid-way
        #      (e.g. by an <a>-wrapped keyword).  Merge the current line.
        #      Short prev lines (<= 55 chars) are typically headings/labels
        #      and should NOT trigger this rule.
        #
        # Tweet-ending detection: Lines ending with a tweet date attribution
        # (e.g. "...February 22, 2026") are treated as sentence-ending so
        # that subsequent headings or article text don't get merged into them.
        _SENTENCE_END = frozenset('.!?;»"')
        _TWEET_DATE_RE = re.compile(
            r"\b(?:January|February|March|April|May|June|July|August"
            r"|September|October|November|December)\s+\d{1,2},\s+\d{4}$"
        )

        merged: list[str] = []
        for line in lines:
            if not merged:
                merged.append(line)
                continue

            first_char = line[0]
            prev = merged[-1]
            prev_ends_sentence = (
                prev[-1:] in _SENTENCE_END
                or bool(_TWEET_DATE_RE.search(prev))
            )

            is_continuation = first_char in (",", ";", "·", ".", "(", ")", "]") or first_char.islower()
            is_orphan_keyword = (
                len(line) < 60
                and not prev_ends_sentence
                and line[-1:] not in _SENTENCE_END
            )
            is_sentence_continuation = (
                not prev_ends_sentence
                and not is_continuation
                and len(prev) > 55
            )

            if is_continuation or is_orphan_keyword or is_sentence_continuation:
                sep = "" if first_char in (",", ";", "·", ".", "!", "?", "(", ")", "]") else " "
                merged[-1] += sep + line
            else:
                merged.append(line)

        # -- 9. Combine any remaining split tweet fragments -------------------
        # With tweet blockquotes pre-flattened, most fragments are already
        # joined.  This catches edge cases where a fragment slips through
        # (e.g. a bare pic.twitter.com/ line or attribution line).
        final: list[str] = []
        for line in merged:
            if final and (
                line.startswith("pic.twitter.com/")
                or line.startswith("— ")
                or line.startswith("— ")   # em-dash variant
                or re.match(r"^https?://t\.co/", line)
            ):
                final[-1] += " " + line
            else:
                final.append(line)

        return "\n\n".join(final).strip()

    def _build_record(
        self,
        candidate: dict,
        result: CrawlResult,
        scraped_at: str,
    ) -> dict:
        """Assemble the final output record from sitemap metadata + crawled content."""
        return {
            "source":       self.source_name,
            "url":          candidate["url"],
            "title":        candidate["title"],
            "body":         self._extract_article_body(result),
            "published_at": candidate["published_at"],
            "scraped_at":   scraped_at,
            "lang":         "el",
            "category_hint": None,
        }
