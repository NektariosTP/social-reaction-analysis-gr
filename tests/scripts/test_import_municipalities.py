from scripts.import_municipalities import (
    missing_gold_municipalities,
    validate_municipalities,
)


def _feature(name: str = "Δήμος Αθηναίων", geom_type: str = "Polygon") -> dict:
    ring = [[23.7, 37.9], [23.8, 37.9], [23.8, 38.0], [23.7, 38.0], [23.7, 37.9]]
    coordinates = [ring] if geom_type == "Polygon" else [[ring]]
    geometry = {"type": geom_type, "coordinates": coordinates}
    return {"type": "Feature", "properties": {"name": name}, "geometry": geometry}


def test_validate_accepts_clean_data() -> None:
    data = {"type": "FeatureCollection", "features": [_feature() for _ in range(300)]}
    assert validate_municipalities(data) == []


def test_validate_flags_too_few_features() -> None:
    data = {"type": "FeatureCollection", "features": [_feature() for _ in range(10)]}
    violations = validate_municipalities(data)
    assert any("only 10" in v for v in violations)


def test_validate_flags_missing_name_and_bad_geometry_type() -> None:
    bad = {
        "type": "FeatureCollection",
        "features": [_feature() for _ in range(299)]
        + [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {"type": "Point", "coordinates": [23.7, 37.9]},
            }
        ],
    }
    violations = validate_municipalities(bad)
    assert any("missing properties.name" in v for v in violations)
    assert any("geometry type Point" in v for v in violations)


def test_missing_gold_municipalities_flags_uncovered_names() -> None:
    data = {"type": "FeatureCollection", "features": [_feature("Δήμος Αθηναίων")]}
    gold = {"Δήμος Αθηναίων", "Δήμος Θεσσαλονίκης"}
    assert missing_gold_municipalities(data, gold) == ["Δήμος Θεσσαλονίκης"]


def test_missing_gold_municipalities_empty_when_all_covered() -> None:
    data = {"type": "FeatureCollection", "features": [_feature("Δήμος Αθηναίων")]}
    assert missing_gold_municipalities(data, {"Δήμος Αθηναίων"}) == []
