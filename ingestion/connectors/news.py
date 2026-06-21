"""Google News RSS connector: keyword queries → trafilatura article extraction."""
from __future__ import annotations

import asyncio
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
import trafilatura
from googlenewsdecoder import new_decoderv1

from ingestion.connectors.base import SourceConnector
from ingestion.models import RawDocument

logger = logging.getLogger(__name__)

_RSS_URL = "https://news.google.com/rss/search?q={query}&hl=el&gl=GR&ceid=GR:el"
_MAX_PER_KEYWORD = 15
_MIN_BODY_LEN = 50
_DECODE_DELAY = 0.5

_RSS_HEADERS = {
    "User-Agent": "SocialReactionAnalysisBot/1.0",
    "Accept": "application/rss+xml, application/xml, */*",
}
_ARTICLE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*",
    "Accept-Language": "el-GR,el;q=0.9,en;q=0.8",
}

_DEFAULT_KEYWORDS_PATH = Path(__file__).parent.parent / "filters" / "keywords.yml"


def _default_keywords() -> list[str]:
    import yaml
    raw: dict[str, list[str]] = yaml.safe_load(
        _DEFAULT_KEYWORDS_PATH.read_text(encoding="utf-8")
    )
    return [kw for group in raw.values() for kw in group]


def _encode_kw(keyword: str) -> str:
    return quote(f'"{keyword}"') if " " in keyword else quote(keyword)


def _parse_pubdate(raw: str) -> datetime | None:
    try:
        return parsedate_to_datetime(raw).replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _strip_source_suffix(title: str, source: str) -> str:
    suffix = f" - {source}"
    return title[: -len(suffix)].strip() if title.endswith(suffix) else title


async def _decode_url(google_url: str) -> str | None:
    try:
        result = await asyncio.to_thread(new_decoderv1, google_url)
        if result.get("status"):
            return str(result["decoded_url"])
        logger.debug("[news] decode failed: %s — %s", google_url, result.get("message"))
    except Exception as exc:
        logger.debug("[news] decode exception for %s: %s", google_url, exc)
    return None


class GoogleNewsConnector(SourceConnector):
    def __init__(
        self,
        keywords: list[str] | None = None,
        request_delay: float = 2.0,
    ) -> None:
        self._keywords = keywords if keywords is not None else _default_keywords()
        self._delay = request_delay

    async def fetch(self) -> list[RawDocument]:
        candidates = await self._collect_candidates()
        logger.info("[news] %d unique candidates after URL decode", len(candidates))
        return await self._fetch_articles(candidates)

    async def _collect_candidates(self) -> list[dict[str, Any]]:
        seen_google: set[str] = set()
        google_candidates: list[dict[str, Any]] = []

        async with httpx.AsyncClient(headers=_RSS_HEADERS, timeout=15.0) as client:
            for i, kw in enumerate(self._keywords):
                if i > 0:
                    await asyncio.sleep(self._delay)
                url = _RSS_URL.format(query=_encode_kw(kw))
                new_items = await self._fetch_rss(url, kw, client)
                for item in new_items[:_MAX_PER_KEYWORD]:
                    if item["url"] not in seen_google:
                        seen_google.add(item["url"])
                        google_candidates.append(item)

        seen_canonical: set[str] = set()
        resolved: list[dict[str, Any]] = []
        for i, candidate in enumerate(google_candidates):
            if i > 0:
                await asyncio.sleep(_DECODE_DELAY)
            canonical = await _decode_url(candidate["url"])
            if canonical is None or canonical in seen_canonical:
                continue
            seen_canonical.add(canonical)
            candidate["url"] = canonical
            resolved.append(candidate)

        return resolved

    @staticmethod
    async def _fetch_rss(
        rss_url: str, keyword: str, client: httpx.AsyncClient
    ) -> list[dict[str, Any]]:
        try:
            resp = await client.get(rss_url, follow_redirects=True)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
        except Exception as exc:
            logger.warning("[news] RSS fetch/parse failed for %r: %s", keyword, exc)
            return []

        channel = root.find("channel")
        if channel is None:
            return []

        items: list[dict[str, Any]] = []
        for item in channel.findall("item"):
            link = (item.findtext("link") or "").strip()
            if not link:
                guid_el = item.find("guid")
                link = (guid_el.text or "").strip() if guid_el is not None else ""
            if not link:
                continue
            source_el = item.find("source")
            source_name = source_el.text.strip() if source_el is not None and source_el.text else ""
            title = _strip_source_suffix((item.findtext("title") or "").strip(), source_name)
            pubdate = _parse_pubdate((item.findtext("pubDate") or "").strip())
            items.append({"url": link, "title": title, "published_at": pubdate})
        return items

    async def _fetch_articles(self, candidates: list[dict[str, Any]]) -> list[RawDocument]:
        docs: list[RawDocument] = []
        async with httpx.AsyncClient(
            headers=_ARTICLE_HEADERS, timeout=20.0, follow_redirects=True
        ) as client:
            for i, candidate in enumerate(candidates):
                if i > 0:
                    await asyncio.sleep(self._delay)
                body = await self._extract_body(candidate["url"], client)
                if body is None:
                    logger.warning("[news] no body extracted for %s", candidate["url"])
                    continue
                docs.append(
                    RawDocument(
                        source_id="google_news_rss",
                        source_type="rss",
                        url=candidate["url"],
                        canonical_url=candidate["url"],
                        title=candidate["title"],
                        body_text=body,
                        language="el",
                        published_at=candidate["published_at"],
                    )
                )
        return docs

    @staticmethod
    async def _extract_body(url: str, client: httpx.AsyncClient) -> str | None:
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                body = trafilatura.extract(
                    resp.text, include_comments=False, include_tables=False
                )
                if body and len(body.strip()) >= _MIN_BODY_LEN:
                    return body.strip()
        except Exception as exc:
            logger.debug("[news] httpx/trafilatura failed for %s: %s", url, exc)
        return None
