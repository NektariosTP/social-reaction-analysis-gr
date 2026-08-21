"""Add region_indicators table (regional statistics/context layer).

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-21
"""
from __future__ import annotations

from alembic import op

revision: str = "0006"
down_revision: str = "0005"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE region_indicators (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            region_code TEXT NOT NULL,
            indicator   TEXT NOT NULL,
            period      TEXT NOT NULL,
            value       NUMERIC,
            unit        TEXT,
            source      TEXT NOT NULL,
            source_url  TEXT,
            released_at DATE,
            fetched_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (region_code, indicator, period)
        )
    """)
    op.execute("CREATE INDEX ix_region_indicators_region ON region_indicators (region_code)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS region_indicators")
