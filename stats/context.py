from __future__ import annotations

from stats.catalog import IndicatorSpec


def _value_dict(spec: IndicatorSpec, row: dict) -> dict:
    return {
        "key": spec.key, "label_el": spec.label_el, "label_en": spec.label_en,
        "unit": spec.unit, "value": float(row["value"]) if row["value"] is not None else None,
        "period": row["period"], "source": row["source"], "source_url": row["source_url"],
    }


def assemble(
    catalog: list[IndicatorSpec],
    value_rows: list[dict],
    thematic_fields: list[str] | None = None,
) -> tuple[list[dict], list[dict]]:
    by_key = {s.key: s for s in catalog}
    themes = set(thematic_fields or [])
    always_on: list[dict] = []
    thematic: list[dict] = []
    for row in value_rows:
        spec = by_key.get(row["indicator"])
        if spec is None:
            continue
        item = _value_dict(spec, row)
        if spec.always_on:
            always_on.append(item)
        elif themes and (set(spec.themes) & themes):
            thematic.append(item)
    return always_on, thematic
