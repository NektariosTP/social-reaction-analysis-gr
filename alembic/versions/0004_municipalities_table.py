"""Add municipalities table (Kallikratis δήμος polygons) + events/event_locations.municipality.

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-05
"""
from __future__ import annotations

from alembic import op

revision: str = "0004"
down_revision: str = "0003"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE municipalities (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name        TEXT NOT NULL,
            region_code TEXT,
            geom        GEOGRAPHY(MultiPolygon, 4326) NOT NULL
        )
    """)
    op.execute("CREATE INDEX ON municipalities USING GIST (geom)")
    op.execute("ALTER TABLE events ADD COLUMN IF NOT EXISTS municipality TEXT")
    op.execute("ALTER TABLE event_locations ADD COLUMN IF NOT EXISTS municipality TEXT")


def downgrade() -> None:
    op.execute("ALTER TABLE event_locations DROP COLUMN IF EXISTS municipality")
    op.execute("ALTER TABLE events DROP COLUMN IF EXISTS municipality")
    op.execute("DROP TABLE IF EXISTS municipalities")
