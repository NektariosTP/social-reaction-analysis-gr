"""Allow deleting events with linked articles: articles.event_id ON DELETE SET NULL.

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-15
"""

from __future__ import annotations

from alembic import op

revision: str = "0003"
down_revision: str = "0002"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE articles DROP CONSTRAINT articles_event_id_fkey")
    op.execute(
        "ALTER TABLE articles "
        "ADD CONSTRAINT articles_event_id_fkey "
        "FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE SET NULL"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE articles DROP CONSTRAINT articles_event_id_fkey")
    op.execute(
        "ALTER TABLE articles "
        "ADD CONSTRAINT articles_event_id_fkey "
        "FOREIGN KEY (event_id) REFERENCES events(id)"
    )
