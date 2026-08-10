"""Add events.event_time (TIMESTAMPTZ) + events.is_national (BOOLEAN) for M8.

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-10
"""
from __future__ import annotations

from alembic import op

revision: str = "0005"
down_revision: str = "0004"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE events ADD COLUMN IF NOT EXISTS event_time TIMESTAMPTZ")
    op.execute(
        "ALTER TABLE events ADD COLUMN IF NOT EXISTS is_national BOOLEAN NOT NULL DEFAULT FALSE"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE events DROP COLUMN IF EXISTS is_national")
    op.execute("ALTER TABLE events DROP COLUMN IF EXISTS event_time")
