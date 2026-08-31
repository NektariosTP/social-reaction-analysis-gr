"""Drop event_reactions.stance — stance abandoned for a derived participation roster.

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-31
"""
from __future__ import annotations

from alembic import op

revision: str = "0008"
down_revision: str = "0007"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE event_reactions DROP COLUMN IF EXISTS stance")


def downgrade() -> None:
    op.execute("ALTER TABLE event_reactions ADD COLUMN stance TEXT NOT NULL DEFAULT 'unknown'")
