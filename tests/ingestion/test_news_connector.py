"""Tests for GoogleNewsConnector."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import respx
from httpx import Response

from ingestion.connectors.news import GoogleNewsConnector

_FIXTURES = Path(__file__).parent / "fixtures"
_RSS_XML = (_FIXTURES / "googlenews_rss.xml").read_text(encoding="utf-8")
_ARTICLE_HTML = (_FIXTURES / "article_body.html").read_text(encoding="utf-8")
_DECODED_URL = "https://www.eleftherotypia.gr/news/article/1234567"
_GOOGLE_URL = (
    "https://news.google.com/rss/articles/"
    "CBMiXmh0dHBzOi8vd3d3LmVsZXV0aGVyb3R5cGlhLmdyL25ld3MvYXJ0aWNsZS8xMjM0NTY3?oc=5"
)


@pytest.fixture
def mock_decoder():
    with patch(
        "ingestion.connectors.news.new_decoderv1",
        return_value={"status": True, "decoded_url": _DECODED_URL},
    ) as m:
        yield m


@respx.mock
async def test_fetch_returns_raw_documents(mock_decoder) -> None:
    respx.get(url__startswith="https://news.google.com/rss/search").mock(
        return_value=Response(200, text=_RSS_XML)
    )
    respx.get(_DECODED_URL).mock(return_value=Response(200, text=_ARTICLE_HTML))

    connector = GoogleNewsConnector(keywords=["απεργία"], request_delay=0.0)
    docs = await connector.fetch()

    assert len(docs) == 1
    assert docs[0].source_id == "google_news_rss"
    assert docs[0].source_type == "rss"
    assert docs[0].language == "el"
    assert docs[0].canonical_url == _DECODED_URL
    assert len(docs[0].content_hash) == 64  # SHA-256 hex digest


@respx.mock
async def test_fetch_deduplicates_by_canonical_url(mock_decoder) -> None:
    # Two keywords return the same article via the same Google News URL
    rss_two_items = _RSS_XML.replace(
        "</channel>",
        """<item>
          <title>Duplicate - Ελευθεροτυπία</title>
          <link>""" + _GOOGLE_URL + """</link>
          <pubDate>Fri, 13 Jun 2026 09:00:00 GMT</pubDate>
        </item></channel>""",
    )
    respx.get(url__startswith="https://news.google.com/rss/search").mock(
        return_value=Response(200, text=rss_two_items)
    )
    respx.get(_DECODED_URL).mock(return_value=Response(200, text=_ARTICLE_HTML))

    connector = GoogleNewsConnector(keywords=["απεργία", "διαδήλωση"], request_delay=0.0)
    docs = await connector.fetch()

    assert len(docs) == 1  # deduplicated


@respx.mock
async def test_fetch_skips_failed_url_decode() -> None:
    respx.get(url__startswith="https://news.google.com/rss/search").mock(
        return_value=Response(200, text=_RSS_XML)
    )
    with patch(
        "ingestion.connectors.news.new_decoderv1",
        return_value={"status": False, "message": "decode error"},
    ):
        connector = GoogleNewsConnector(keywords=["απεργία"], request_delay=0.0)
        docs = await connector.fetch()

    assert docs == []


@respx.mock
async def test_fetch_skips_rss_network_error() -> None:
    respx.get(url__startswith="https://news.google.com/rss/search").mock(
        return_value=Response(503)
    )
    connector = GoogleNewsConnector(keywords=["απεργία"], request_delay=0.0)
    docs = await connector.fetch()
    assert docs == []
