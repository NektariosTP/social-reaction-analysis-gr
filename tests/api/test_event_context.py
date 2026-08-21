import pytest
from unittest.mock import MagicMock


def _result(rows):
    m = MagicMock()
    m.all.return_value = rows
    m.first.return_value = rows[0] if rows else None
    return m


async def test_event_context_matches_theme(client):
    from api.main import app
    from api.db import get_db
    # the conftest override yields one shared AsyncMock session:
    gen = app.dependency_overrides[get_db]()
    session = await gen.__anext__()

    event_row = ("Αττική", ["Οικονομικό"])        # (region_code, thematic_fields)
    indicator_rows = [
        ("gdp_per_capita", 20000, "EUR", "2022", "eurostat", "http://x"),
        ("at_risk_of_poverty", 25, "%", "2022", "eurostat", "http://x"),
        ("rule_of_law", 70, "pctile", "2023", "worldbank", "http://x"),
    ]
    session.execute.side_effect = [_result([event_row]), _result(indicator_rows)]

    resp = await client.get("/events/abc/context")
    assert resp.status_code == 200
    body = resp.json()
    keys_always = {i["key"] for i in body["always_on"]}
    keys_thematic = {i["key"] for i in body["thematic"]}
    assert "gdp_per_capita" in keys_always
    assert "at_risk_of_poverty" in keys_thematic       # Οικονομικό match
    assert "rule_of_law" not in keys_thematic          # not an Οικονομικό indicator


async def test_event_context_404(client):
    from api.main import app
    from api.db import get_db
    gen = app.dependency_overrides[get_db]()
    session = await gen.__anext__()
    session.execute.side_effect = [_result([])]        # no event
    resp = await client.get("/events/missing/context")
    assert resp.status_code == 404
