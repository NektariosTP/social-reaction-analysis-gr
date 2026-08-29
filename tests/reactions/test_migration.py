from pathlib import Path

MIGRATION = Path("alembic/versions/0007_event_reactions.py").read_text(encoding="utf-8")


def test_migration_creates_table_and_columns():
    for col in [
        "event_reactions", "source_org", "actor_name", "actor_role",
        "stance", "observed_at", "match_score", "match_method",
    ]:
        assert col in MIGRATION
    assert "UNIQUE (source_org, url)" in MIGRATION
    assert 'down_revision: str = "0006"' in MIGRATION
