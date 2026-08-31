# tests/enrich/test_gazetteer.py
"""Gazetteer named-venue + word-boundary matching (see
docs/superpowers/specs/2026-08-31-gazetteer-aliases-word-boundary-design.md)."""
from enrich.geocode import lookup_gazetteer

CITY_THESS = (40.6401, 22.9444)  # Θεσσαλονίκη city centroid in the gazetteer


def test_deth_resolves_to_own_venue_point():
    r = lookup_gazetteer("Συλλαλητήριο στη ΔΕΘ")
    assert r is not None
    assert r.location_name == "Διεθνής Έκθεση Θεσσαλονίκης (ΔΕΘ)"
    # its OWN point, not folded into the generic city centroid
    assert (r.lat, r.lon) != CITY_THESS


def test_midword_acronym_not_matched():
    # 'δεθ' lives inside 'συνδεθείτε' — leading word boundary must reject it
    assert lookup_gazetteer("Παρακαλούμε συνδεθείτε στο σύστημα") is None


def test_inflected_city_still_matches():
    r = lookup_gazetteer("Ιπποκράτειο Νοσοκομείο Θεσσαλονίκης")  # genitive
    assert r is not None and r.location_name == "Θεσσαλονίκη"
    assert (r.lat, r.lon) == CITY_THESS


def test_spelled_out_venue_falls_back_to_city():
    # multi-word inflected phrase isn't a surface form; resolves via embedded city
    r = lookup_gazetteer("εγκαίνια στη Διεθνή Έκθεση Θεσσαλονίκης")
    assert r is not None and r.location_name == "Θεσσαλονίκη"


def test_plain_city_unchanged():
    assert lookup_gazetteer("Συγκέντρωση στη Θεσσαλονίκη").location_name == "Θεσσαλονίκη"
    assert lookup_gazetteer("Πορεία στην Αθήνα αύριο").location_name == "Αθήνα"


def test_panathinaikos_not_athens():
    # mid-word 'αθην' must not resolve to Αθήνα
    assert lookup_gazetteer("Παναθηναϊκός αγώνας") is None
