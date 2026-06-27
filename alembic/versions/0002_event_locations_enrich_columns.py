"""Add location_name, city, is_primary to event_locations.

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-27
"""

from __future__ import annotations

from alembic import op

revision: str = "0002"
down_revision: str = "0001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE event_locations ADD COLUMN IF NOT EXISTS location_name TEXT")
    op.execute("ALTER TABLE event_locations ADD COLUMN IF NOT EXISTS city TEXT")
    op.execute(
        "ALTER TABLE event_locations ADD COLUMN IF NOT EXISTS is_primary BOOL NOT NULL DEFAULT TRUE"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE event_locations DROP COLUMN IF EXISTS is_primary")
    op.execute("ALTER TABLE event_locations DROP COLUMN IF EXISTS city")
    op.execute("ALTER TABLE event_locations DROP COLUMN IF EXISTS location_name")
