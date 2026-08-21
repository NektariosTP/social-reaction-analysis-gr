from unittest.mock import AsyncMock

import pytest

from stats.catalog import IndicatorSpec
from stats.models import IndicatorRow
from stats.refresh import refresh, row_params, UPSERT_SQL


def _spec(key, source):
    return IndicatorSpec(key=key, label_el="x", label_en="x", unit="%",
                         source=source, dataset="D", geo_level="national",
                         cadence="annual", always_on=False, themes=())


class _FakeSource:
    def __init__(self, name, rows=None, exc=None):
        self.source_name = name
        self._rows = rows or []
        self._exc = exc
    async def fetch(self, spec, client):
        if self._exc:
            raise self._exc
        return self._rows


def test_row_params_maps_all_columns():
    r = IndicatorRow("Attica", "gdp", "2022", 110.0, "EUR", "eurostat", "http://x")
    p = row_params(r)
    assert p["region_code"] == "Attica" and p["value"] == 110.0
    assert set(p) == {"region_code", "indicator", "period", "value", "unit", "source", "source_url", "released_at"}
    assert "ON CONFLICT" in UPSERT_SQL


async def test_refresh_isolates_failing_source():
    session = AsyncMock()
    ok_row = IndicatorRow("GR", "rule_of_law", "2023", 70.0, "pctile", "worldbank", "http://x")
    sources = {
        "worldbank": _FakeSource("worldbank", rows=[ok_row]),
        "eurostat": _FakeSource("eurostat", exc=RuntimeError("boom")),
    }
    specs = [_spec("rule_of_law", "worldbank"), _spec("gdp_per_capita", "eurostat")]
    result = await refresh(session, client=None, specs=specs, sources=sources)
    assert result["rule_of_law"] == 1
    assert result["gdp_per_capita"] == 0   # failed, isolated
    assert session.execute.await_count == 1  # only the ok row upserted
