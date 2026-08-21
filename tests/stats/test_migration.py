from pathlib import Path


def test_migration_0006_defines_region_indicators():
    src = Path("alembic/versions/0006_region_indicators.py").read_text(encoding="utf-8")
    assert 'CREATE TABLE region_indicators' in src
    assert 'UNIQUE (region_code, indicator, period)' in src
    assert 'down_revision: str = "0005"' in src
    assert 'DROP TABLE IF EXISTS region_indicators' in src  # downgrade
