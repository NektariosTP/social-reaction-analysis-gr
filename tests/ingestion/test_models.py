"""Tests for RawDocument model."""
import hashlib

import pytest

from ingestion.models import RawDocument


def test_content_hash_is_computed_from_canonical_url_and_title() -> None:
    doc = RawDocument(
        source_id="googlenews",
        source_type="rss",
        url="https://example.com/article",
        canonical_url="https://example.com/article",
        title="Απεργία στο Μετρό",
        body_text="Κείμενο άρθρου",
        language="el",
        published_at=None,
    )
    expected = hashlib.sha256(
        "https://example.com/article|απεργία στο μετρό".encode()
    ).hexdigest()
    assert doc.content_hash == expected


def test_content_hash_is_stable_across_instances() -> None:
    kwargs = dict(
        source_id="a",
        source_type="rss",
        url="https://x.com/p",
        canonical_url="https://x.com/p",
        title="Διαδήλωση",
        body_text="body1",
        language="el",
        published_at=None,
    )
    doc1 = RawDocument(**kwargs)
    doc2 = RawDocument(**{**kwargs, "body_text": "body2"})  # different body, same hash
    assert doc1.content_hash == doc2.content_hash


def test_content_hash_differs_for_different_titles() -> None:
    base = dict(source_id="s", source_type="rss", url="u", canonical_url="u",
                body_text="b", language="el", published_at=None)
    doc1 = RawDocument(**{**base, "title": "Απεργία"})
    doc2 = RawDocument(**{**base, "title": "Διαδήλωση"})
    assert doc1.content_hash != doc2.content_hash


def test_explicit_content_hash_is_preserved() -> None:
    doc = RawDocument(
        source_id="s", source_type="rss", url="u", canonical_url="u",
        title="T", body_text="b", language="el", published_at=None,
        content_hash="abc123",
    )
    assert doc.content_hash == "abc123"
