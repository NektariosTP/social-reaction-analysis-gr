"""Config-driven union-feed connector. Parses RSS/Atom → ReactionItem (never RawDocument)."""
from __future__ import annotations

import asyncio
import logging
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

import httpx
import yaml
from pydantic import BaseModel

logger = logging.getLogger(__name__)

_SOURCES_PATH = Path(__file__).parent.parent / "sources" / "unions.yml"
_ATOM_NS = {"a": "http://www.w3.org/2005/Atom"}
_HEADERS = {
    "User-Agent": "SocialReactionAnalysisBot/1.0",
    "Accept": "application/rss+xml, application/atom+xml, application/xml, */*",
    "Accept-Language": "el-GR,el;q=0.9,en;q=0.8",
}


class ReactionItem(BaseModel):
    source_org: str
    actor_name: str
    title: str
    body_text: str
    url: str
    observed_at: datetime | None


def load_union_sources(path: Path | None = None) -> list[dict]:
    raw = yaml.safe_load((path or _SOURCES_PATH).read_text(encoding="utf-8"))
    # Normalize the key the connector consumes: org_slug is the config's stable slug.
    return raw or []


def _parse_pubdate(raw: str) -> datetime | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:  # RSS pubDate (RFC-822)
        return parsedate_to_datetime(raw).astimezone(UTC)
    except Exception:
        pass
    try:  # Atom published/updated (ISO-8601)
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(UTC)
    except Exception:
        return None


def parse_feed(source_org: str, actor_name: str, raw: bytes) -> list[ReactionItem]:
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        logger.warning("[union:%s] XML parse failed: %s", source_org, exc)
        return []

    items: list[ReactionItem] = []
    rss_items = root.findall(".//item")
    if rss_items:
        for it in rss_items:
            link = (it.findtext("link") or "").strip()
            if not link:
                guid = it.find("guid")
                link = (guid.text or "").strip() if guid is not None else ""
            if not link:
                continue
            items.append(ReactionItem(
                source_org=source_org, actor_name=actor_name,
                title=(it.findtext("title") or "").strip(),
                body_text=(it.findtext("description") or "").strip(),
                url=link,
                observed_at=_parse_pubdate(it.findtext("pubDate") or ""),
            ))
        return items

    for e in root.findall(".//a:entry", _ATOM_NS):  # Atom fallback
        link_el = e.find("a:link", _ATOM_NS)
        link = (link_el.get("href") if link_el is not None else "") or ""
        if not link:
            continue
        body = e.findtext("a:summary", default="", namespaces=_ATOM_NS) \
            or e.findtext("a:content", default="", namespaces=_ATOM_NS)
        pub = e.findtext("a:published", default="", namespaces=_ATOM_NS) \
            or e.findtext("a:updated", default="", namespaces=_ATOM_NS)
        items.append(ReactionItem(
            source_org=source_org, actor_name=actor_name,
            title=e.findtext("a:title", default="", namespaces=_ATOM_NS).strip(),
            body_text=(body or "").strip(), url=link.strip(),
            observed_at=_parse_pubdate(pub),
        ))
    return items


class UnionFeedConnector:
    def __init__(self, source_org: str, actor_name: str, feed_url: str,
                 feed_format: str = "rss", request_delay: float = 2.0) -> None:
        self.source_org = source_org
        self.actor_name = actor_name
        self.feed_url = feed_url
        self.feed_format = feed_format
        self._delay = request_delay

    async def fetch(self) -> list[ReactionItem]:
        async with httpx.AsyncClient(headers=_HEADERS, timeout=20.0, follow_redirects=True) as client:
            try:
                resp = await client.get(self.feed_url)
                resp.raise_for_status()
            except Exception as exc:
                logger.warning("[union:%s] fetch failed: %s", self.source_org, exc)
                return []
        await asyncio.sleep(0)  # yield; per-feed pacing handled by caller
        return parse_feed(self.source_org, self.actor_name, resp.content)
