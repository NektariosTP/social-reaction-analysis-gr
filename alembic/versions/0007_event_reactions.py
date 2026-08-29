"""Add event_reactions table (union-statement reactions / announced-event seeds).

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-27
"""
from __future__ import annotations

from alembic import op

revision: str = "0007"
down_revision: str = "0006"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE event_reactions (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            event_id      UUID REFERENCES events(id) ON DELETE SET NULL,
            source_org    TEXT NOT NULL,
            actor_name    TEXT NOT NULL,
            actor_role    TEXT NOT NULL DEFAULT 'union',
            stance        TEXT NOT NULL DEFAULT 'unknown',
            text          TEXT NOT NULL,
            url           TEXT NOT NULL,
            observed_at   TIMESTAMPTZ,
            match_score   DOUBLE PRECISION,
            match_method  TEXT NOT NULL DEFAULT 'none',
            created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (source_org, url)
        )
    """)
    op.execute("CREATE INDEX ON event_reactions (event_id)")
    op.execute("CREATE INDEX ON event_reactions (source_org, observed_at)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS event_reactions")
