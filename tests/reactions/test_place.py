# tests/reactions/test_place.py
from reactions.place import resolve_place, PlaceResult


def test_national_flag_set():
    r = resolve_place("Πανελλαδικό Συλλαλητήριο 5 Σεπτέμβρη")
    assert isinstance(r, PlaceResult)
    assert r.is_national is True


def test_gazetteer_city_resolves_coords():
    r = resolve_place("Συγκέντρωση στη Θεσσαλονίκη")
    # Thessaloniki is in the shipped gazetteer; coords populated.
    assert r.name is not None and r.lat is not None and r.lon is not None


def test_unknown_place_returns_empty_coords():
    r = resolve_place("Ενημέρωση αιρετού")
    assert r.lat is None and r.is_national is False
