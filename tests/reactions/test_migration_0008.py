from pathlib import Path

MIGRATION = Path("alembic/versions/0008_drop_reaction_stance.py").read_text(encoding="utf-8")


def test_migration_drops_stance_and_chains_from_0007():
    assert 'down_revision: str = "0007"' in MIGRATION
    assert "DROP COLUMN" in MIGRATION and "stance" in MIGRATION
