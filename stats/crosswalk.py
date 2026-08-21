"""NUTS2 (EL-code) ↔ canonical periphery-name crosswalk, sourced from
enrich/data/regions.geojson (the one canonical periphery registry)."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_REGIONS_PATH = Path(__file__).resolve().parent.parent / "enrich" / "data" / "regions.geojson"


@lru_cache(maxsize=1)
def _features() -> list[dict]:
    return json.loads(_REGIONS_PATH.read_text(encoding="utf-8"))["features"]


@lru_cache(maxsize=1)
def nuts2_to_name() -> dict[str, str]:
    out: dict[str, str] = {}
    for f in _features():
        p = f["properties"]
        code = p.get("nuts2")
        if code:
            out[code] = p["name"]
    return out


@lru_cache(maxsize=1)
def name_to_nuts2() -> dict[str, str]:
    return {name: code for code, name in nuts2_to_name().items()}


@lru_cache(maxsize=1)
def _alias_map() -> dict[str, str]:
    """lower-cased English name + Greek name → canonical English name."""
    aliases: dict[str, str] = {}
    for f in _features():
        p = f["properties"]
        name = p["name"]
        aliases[name.lower()] = name
        greek = p.get("name_greek")
        if greek:
            aliases[greek.lower()] = name
    return aliases


def canonical_region_name(raw: str | None) -> str | None:
    if not raw:
        return None
    return _alias_map().get(raw.strip().lower())
