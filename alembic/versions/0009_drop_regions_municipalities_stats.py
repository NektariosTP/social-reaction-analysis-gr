"""Drop peripheries/municipalities/statistics layer.

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-09
"""
from __future__ import annotations

from alembic import op

revision: str = "0009"
down_revision: str = "0008"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS region_indicators")
    op.execute("DROP TABLE IF EXISTS municipalities")
    op.execute("ALTER TABLE events DROP COLUMN IF EXISTS region_code")
    op.execute("ALTER TABLE events DROP COLUMN IF EXISTS municipality")
    op.execute("ALTER TABLE event_locations DROP COLUMN IF EXISTS region_code")
    op.execute("ALTER TABLE event_locations DROP COLUMN IF EXISTS municipality")


def downgrade() -> None:
    # Irreversible on data (as agreed). Re-add nullable columns so schema shape
    # can be restored; the dropped tables are not recreated here.
    op.execute("ALTER TABLE events ADD COLUMN IF NOT EXISTS region_code TEXT")
    op.execute("ALTER TABLE events ADD COLUMN IF NOT EXISTS municipality TEXT")
    op.execute("ALTER TABLE event_locations ADD COLUMN IF NOT EXISTS region_code TEXT")
    op.execute("ALTER TABLE event_locations ADD COLUMN IF NOT EXISTS municipality TEXT")
