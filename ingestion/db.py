"""Async DB helpers for the ingestion pipeline."""

from __future__ import annotations

import uuid as uuid_mod

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ingestion.models import RawDocument


async def upsert_article(doc: RawDocument, session: AsyncSession) -> bool:
    """Insert article; return True if inserted, False if duplicate.

    `content_hash` and `canonical_url` both have their own UNIQUE constraints,
    but Postgres only allows one ON CONFLICT arbiter per statement, so a
    canonical_url collision (e.g. the same article re-fetched with a slightly
    different title) still raises IntegrityError. Runs inside a SAVEPOINT so
    that failure doesn't poison the caller's outer transaction.
    """
    try:
        async with session.begin_nested():
            result = await session.execute(
                text("""
                    INSERT INTO articles (
                        id, source_id, source_type, url, canonical_url,
                        title, body_text, language, published_at, content_hash
                    )
                    VALUES (
                        :id, :source_id, :source_type, :url, :canonical_url,
                        :title, :body_text, :language, :published_at, :content_hash
                    )
                    ON CONFLICT (content_hash) DO NOTHING
                """),
                {
                    "id": str(uuid_mod.uuid4()),
                    "source_id": doc.source_id,
                    "source_type": doc.source_type,
                    "url": doc.url,
                    "canonical_url": doc.canonical_url,
                    "title": doc.title,
                    "body_text": doc.body_text,
                    "language": doc.language,
                    "published_at": doc.published_at,
                    "content_hash": doc.content_hash,
                },
            )
    except IntegrityError:
        return False
    return result.rowcount > 0
