from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

_CATALOG_PATH = Path(__file__).resolve().parent / "indicators.yaml"
_VALID_SOURCES = {"eurostat", "worldbank"}
_VALID_GEO = {"nuts2", "national"}


@dataclass(frozen=True)
class IndicatorSpec:
    key: str
    label_el: str
    label_en: str
    unit: str | None
    source: str
    dataset: str
    geo_level: str
    cadence: str
    always_on: bool
    themes: tuple[str, ...]


@lru_cache(maxsize=4)
def load_catalog(path: str | None = None) -> list[IndicatorSpec]:
    p = Path(path) if path else _CATALOG_PATH
    raw = yaml.safe_load(p.read_text(encoding="utf-8")) or []
    specs: list[IndicatorSpec] = []
    seen: set[str] = set()
    for entry in raw:
        key = entry["key"]
        if key in seen:
            raise ValueError(f"duplicate indicator key: {key}")
        seen.add(key)
        source = entry["source"]
        geo = entry["geo_level"]
        if source not in _VALID_SOURCES:
            raise ValueError(f"{key}: invalid source {source!r}")
        if geo not in _VALID_GEO:
            raise ValueError(f"{key}: invalid geo_level {geo!r}")
        specs.append(IndicatorSpec(
            key=key,
            label_el=entry["label_el"],
            label_en=entry["label_en"],
            unit=entry.get("unit"),
            source=source,
            dataset=entry["dataset"],
            geo_level=geo,
            cadence=entry.get("cadence", "annual"),
            always_on=bool(entry.get("always_on", False)),
            themes=tuple(entry.get("themes") or []),
        ))
    return specs
