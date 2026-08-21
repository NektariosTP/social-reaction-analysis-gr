"""Eurostat dissemination API (JSON-stat 2.0) — regional (NUTS2) indicators."""
from __future__ import annotations

import httpx

from stats.catalog import IndicatorSpec
from stats.crosswalk import nuts2_to_name
from stats.models import IndicatorRow
from stats.sources.base import IndicatorSource

_BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"


def build_url(spec: IndicatorSpec) -> str:
    url = (
        f"{_BASE}/{spec.dataset}"
        f"?format=JSON&lang=EN&geoLevel={spec.geo_level}&sinceTimePeriod=2015"
    )
    for dim, value in spec.filters:
        url += f"&{dim}={value}"
    return url


def _strides(sizes: list[int]) -> list[int]:
    strides = [1] * len(sizes)
    acc = 1
    for i in range(len(sizes) - 1, -1, -1):
        strides[i] = acc
        acc *= sizes[i]
    return strides


def parse_jsonstat(doc: dict, spec: IndicatorSpec) -> list[IndicatorRow]:
    ids: list[str] = doc["id"]
    sizes: list[int] = doc["size"]
    strides = _strides(sizes)
    dims = doc["dimension"]
    geo_index: dict[str, int] = dims["geo"]["category"]["index"]
    time_index: dict[str, int] = dims["time"]["category"]["index"]
    values = doc["value"]
    name_map = nuts2_to_name()

    def value_at(lin: int):
        if isinstance(values, dict):
            return values.get(str(lin))
        return values[lin] if 0 <= lin < len(values) else None

    rows: list[IndicatorRow] = []
    url = build_url(spec)
    for geo_code, gpos in geo_index.items():
        name = name_map.get(geo_code)
        if name is None:  # skip non-GR / aggregates
            continue
        best: tuple[str, float] | None = None
        for tcode, tpos in time_index.items():
            lin = 0
            for i, did in enumerate(ids):
                pos = gpos if did == "geo" else tpos if did == "time" else 0
                lin += pos * strides[i]
            v = value_at(lin)
            if v is None:
                continue
            if best is None or tcode > best[0]:
                best = (tcode, float(v))
        if best is not None:
            rows.append(IndicatorRow(
                region_code=name, indicator=spec.key, period=best[0],
                value=best[1], unit=spec.unit, source="eurostat", source_url=url,
            ))
    return rows


class EurostatSource(IndicatorSource):
    source_name = "eurostat"

    async def fetch(self, spec: IndicatorSpec, client: httpx.AsyncClient) -> list[IndicatorRow]:
        resp = await client.get(build_url(spec), timeout=60)
        resp.raise_for_status()
        return parse_jsonstat(resp.json(), spec)
