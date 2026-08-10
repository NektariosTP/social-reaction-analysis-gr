"""Load Kallikratis δήμος polygons (enrich/data/kallikratis_municipalities.geojson)
into the municipalities table. Run once after `alembic upgrade head` on a fresh DB,
or with --force to replace existing rows.

Usage:
    uv run python scripts/import_municipalities.py
    uv run python scripts/import_municipalities.py --force
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

sys.path.insert(0, str(Path(__file__).parent.parent))
from enrich.config import settings  # noqa: E402
from enrich.geocode import region_for_point  # noqa: E402
from scripts.gold_common import GREEK_TO_EN_REGION, REGION_NAMES, load_jsonl  # noqa: E402

DATA_PATH = (
    Path(__file__).parent.parent / "enrich" / "data" / "kallikratis_municipalities.geojson"
)
GOLD_EVENTS_PATH = (
    Path(__file__).parent.parent / "tests" / "fixtures" / "gold" / "events.jsonl"
)
MIN_MUNICIPALITIES = 300  # sanity floor, not an exact Kallikratis count — sources vary slightly


def _municipality_names(value: object) -> list[str]:
    """Normalize a scalar-or-list true_municipality field to a list of non-empty names."""
    if value is None:
        return []
    return [v for v in (value if isinstance(value, list) else [value]) if v]


def _gold_municipality_names() -> set[str]:
    """Every distinct true_municipality name the eval will score against."""
    names: set[str] = set()
    for record in load_jsonl(GOLD_EVENTS_PATH):
        names.update(_municipality_names(record.get("true_municipality")))
    return names


def missing_gold_municipalities(data: dict, gold_names: set[str]) -> list[str]:
    """Gold true_municipality names not present as a feature `name`, sorted; [] = full coverage.

    Guards the metric's biggest silent failure mode: a source whose δήμος names don't
    match the gold strings (case/prefix/spelling) validates fine but scores muni_accuracy=0.
    This catches the mismatch at import time instead of after a 15–45 min run."""
    have = {
        feature.get("properties", {}).get("name") for feature in data.get("features", [])
    }
    return sorted(name for name in gold_names if name not in have)


def validate_municipalities(data: dict) -> list[str]:
    """Return human-readable violations for a municipalities GeoJSON; [] = valid."""
    violations: list[str] = []
    features = data.get("features", [])
    if len(features) < MIN_MUNICIPALITIES:
        violations.append(
            f"only {len(features)} features, expected at least {MIN_MUNICIPALITIES}"
        )
    for i, feature in enumerate(features):
        props = feature.get("properties", {})
        if not props.get("name"):
            violations.append(f"feature {i}: missing properties.name")
        geom_type = feature.get("geometry", {}).get("type")
        if geom_type not in ("Polygon", "MultiPolygon"):
            violations.append(
                f"feature {i} ({props.get('name', '?')}): geometry type {geom_type}, "
                "expected Polygon/MultiPolygon"
            )
    return violations


def _region_for_feature(feature: dict) -> str | None:
    """Prefer the feature's own region property; fall back to point-in-polygon
    on its first ring's first vertex (cheap, good enough to pick one periphery)."""
    region = feature.get("properties", {}).get("region")
    mapped = GREEK_TO_EN_REGION.get(region, region)
    if mapped in REGION_NAMES:
        return mapped
    geom = feature["geometry"]
    ring = geom["coordinates"][0] if geom["type"] == "Polygon" else geom["coordinates"][0][0]
    lon, lat = ring[0]
    return region_for_point(lat, lon)


async def main(force: bool) -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    violations = validate_municipalities(data)
    missing = missing_gold_municipalities(data, _gold_municipality_names())
    if violations or missing:
        for v in violations:
            print(f"[import_municipalities] INVALID: {v}")
        for m in missing:
            print(f"[import_municipalities] UNCOVERED gold municipality (fix name in GeoJSON): {m!r}")
        raise SystemExit(1)

    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        if force:
            await session.execute(text("DELETE FROM municipalities"))
        inserted = 0
        for feature in data["features"]:
            name = feature["properties"]["name"]
            region_code = _region_for_feature(feature)
            await session.execute(
                text("""
                    INSERT INTO municipalities (name, region_code, geom)
                    VALUES (
                        :name, :region_code,
                        ST_SetSRID(ST_Multi(ST_GeomFromGeoJSON(:geom_json)), 4326)::geography
                    )
                """),
                {
                    "name": name,
                    "region_code": region_code,
                    "geom_json": json.dumps(feature["geometry"]),
                },
            )
            inserted += 1
        await session.commit()
    await engine.dispose()
    print(f"[import_municipalities] inserted {inserted} municipalities (force={force})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="delete existing rows first")
    args = ap.parse_args()
    asyncio.run(main(args.force))
