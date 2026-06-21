"""Initial schema: articles, events, event_locations, pipeline_runs.

Revision ID: 0001
Revises:
Create Date: 2026-06-13
"""

from __future__ import annotations

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.execute("""
        CREATE TABLE pipeline_runs (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            finished_at     TIMESTAMPTZ,
            config_snapshot JSONB NOT NULL DEFAULT '{}',
            metrics         JSONB NOT NULL DEFAULT '{}'
        )
    """)

    op.execute("""
        CREATE TABLE events (
            id                         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            centroid                   vector(768),
            action_forms               TEXT[]    NOT NULL DEFAULT '{}',
            thematic_fields            TEXT[]    NOT NULL DEFAULT '{}',
            channel                    TEXT,
            intensity                  TEXT,
            classification_confidence  JSONB              DEFAULT '{}',
            summary_el                 TEXT,
            summary_en                 TEXT,
            primary_location           GEOGRAPHY(Point, 4326),
            region_code                TEXT,
            article_count              INT       NOT NULL DEFAULT 0,
            source_count               INT       NOT NULL DEFAULT 0,
            first_seen                 TIMESTAMPTZ,
            last_seen                  TIMESTAMPTZ,
            status                     TEXT      NOT NULL DEFAULT 'detected'
        )
    """)

    op.execute("""
        CREATE TABLE articles (
            id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            source_id      TEXT,
            source_type    TEXT,
            url            TEXT,
            canonical_url  TEXT UNIQUE NOT NULL,
            title          TEXT,
            body_text      TEXT,
            language       TEXT,
            published_at   TIMESTAMPTZ,
            content_hash   TEXT UNIQUE NOT NULL,
            ingested_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            embedding      vector(768),
            event_id       UUID REFERENCES events(id),
            is_duplicate   BOOL NOT NULL DEFAULT FALSE
        )
    """)

    op.execute("""
        CREATE TABLE event_locations (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            event_id    UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
            location    GEOGRAPHY(Point, 4326),
            region_code TEXT,
            label       TEXT
        )
    """)

    # Indexes
    op.execute(
        "CREATE INDEX ON articles USING hnsw (embedding vector_cosine_ops)"
        " WITH (m = 16, ef_construction = 64)"
    )
    op.execute(
        "CREATE INDEX ON events USING hnsw (centroid vector_cosine_ops)"
        " WITH (m = 16, ef_construction = 64)"
    )
    op.execute("CREATE INDEX ON articles (event_id)")
    op.execute("CREATE INDEX ON articles (content_hash)")
    op.execute("CREATE INDEX ON event_locations (event_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS event_locations")
    op.execute("DROP TABLE IF EXISTS articles")
    op.execute("DROP TABLE IF EXISTS events")
    op.execute("DROP TABLE IF EXISTS pipeline_runs")
    op.execute("DROP EXTENSION IF EXISTS vector")
    op.execute("DROP EXTENSION IF EXISTS postgis")
