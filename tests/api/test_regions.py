from unittest.mock import MagicMock

from stats.context import assemble
from stats.catalog import load_catalog


def _result(rows):
    m = MagicMock()
    m.all.return_value = rows
    m.first.return_value = rows[0] if rows else None
    return m


def test_assemble_splits_always_on_and_thematic():
    catalog = load_catalog()
    rows = [
        {"indicator": "gdp_per_capita", "value": 20000, "unit": "EUR", "period": "2022",
         "source": "eurostat", "source_url": "http://x"},
        {"indicator": "at_risk_of_poverty", "value": 25, "unit": "%", "period": "2022",
         "source": "eurostat", "source_url": "http://x"},
        {"indicator": "rule_of_law", "value": 70, "unit": "pctile", "period": "2023",
         "source": "worldbank", "source_url": "http://x"},
    ]
    always_on, thematic = assemble(catalog, rows, thematic_fields=["Οικονομικό"])
    assert any(i["key"] == "gdp_per_capita" for i in always_on)          # always_on flag
    assert any(i["key"] == "at_risk_of_poverty" for i in thematic)       # theme match
    assert not any(i["key"] == "rule_of_law" for i in thematic)          # theme miss


async def test_region_indicators_endpoint(client):
    from api.db import get_db
    from api.main import app
    # grab the same AsyncMock session the conftest override yields
    gen = app.dependency_overrides[get_db]()
    session = await gen.__anext__()
    session.execute.return_value = _result([])   # no rows → empty groups (valid response)

    resp = await client.get("/regions/Attica/indicators")
    assert resp.status_code == 200
    body = resp.json()
    assert body["region_code"] == "Attica"
    assert body["always_on"] == [] and body["thematic"] == []


async def test_indicator_catalog_lists_only_nuts2(client):
    resp = await client.get("/stats/indicators")
    assert resp.status_code == 200
    keys = {i["key"] for i in resp.json()["indicators"]}
    # periphery-varying (eurostat/nuts2) indicators are present …
    assert "unemployment_rate" in keys
    assert "gdp_per_capita" in keys
    # … and national (worldbank) indicators are excluded
    assert "gdp_growth" not in keys
    assert "inflation_cpi" not in keys
