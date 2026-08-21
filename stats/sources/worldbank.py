"""World Bank Indicators API — national tier (macro + WGI governance)."""
from __future__ import annotations

import httpx

from stats.catalog import IndicatorSpec
from stats.models import IndicatorRow
from stats.sources.base import IndicatorSource

_BASE = "https://api.worldbank.org/v2"


def build_url(spec: IndicatorSpec) -> str:
    return f"{_BASE}/country/GRC/indicator/{spec.dataset}?format=json&per_page=100&date=2010:2025"


def parse_worldbank(doc: list, spec: IndicatorSpec) -> list[IndicatorRow]:
    if not isinstance(doc, list) or len(doc) < 2 or not doc[1]:
        return []
    url = build_url(spec)
    rows: list[IndicatorRow] = []
    for e in doc[1]:
        val = e.get("value")
        if val is None:
            continue
        rows.append(IndicatorRow(
            region_code="GR", indicator=spec.key, period=str(e.get("date")),
            value=float(val), unit=spec.unit, source="worldbank", source_url=url,
        ))
    return rows


class WorldBankSource(IndicatorSource):
    source_name = "worldbank"

    async def fetch(self, spec: IndicatorSpec, client: httpx.AsyncClient) -> list[IndicatorRow]:
        resp = await client.get(build_url(spec), timeout=60)
        resp.raise_for_status()
        return parse_worldbank(resp.json(), spec)
