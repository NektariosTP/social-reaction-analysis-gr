# tests/reactions/test_place.py
from reactions.place import resolve_place, PlaceResult


def test_national_flag_set():
    r = resolve_place("Πανελλαδικό Συλλαλητήριο 5 Σεπτέμβρη")
    assert isinstance(r, PlaceResult)
    assert r.is_national is True


def test_resolve_place_never_returns_gazetteer_coords():
    r = resolve_place("Συγκέντρωση στη Θεσσαλονίκη αύριο")
    assert r.lat is None and r.lon is None and r.name is None


def test_resolve_place_still_detects_national_scope():
    r = resolve_place("Πανελλαδική πανεργατική απεργία σε όλη τη χώρα")
    assert r.is_national is True


def test_unknown_place_returns_empty_coords():
    r = resolve_place("Ενημέρωση αιρετού")
    assert r.lat is None and r.is_national is False
