from datetime import date

import numpy as np

from reactions.seed import find_announced_duplicate


def _v(x):
    v = np.zeros(768, dtype=np.float32)
    v[0] = x
    return v / np.linalg.norm(v)


# existing tuple: (eid, centroid, seed_org, day, action_forms, lat, lon, is_national)
def test_merge_different_unions_same_national_rally():
    existing = [("evt-1", _v(1), "pame", date(2026, 9, 5),
                 ["Διαδήλωση/Πορεία/Συγκέντρωση"], None, None, True)]
    # A DIFFERENT union (genop), low centroid sim, but same national day+action → merge.
    match = find_announced_duplicate(
        centroid=_v(-1), event_day=date(2026, 9, 5),
        action_forms=["Διαδήλωση/Πορεία/Συγκέντρωση"],
        place_lat=None, place_lon=None, is_national=True,
        existing=existing, sim_threshold=0.9,
    )
    assert match == "evt-1"


def test_merge_same_place_same_day():
    existing = [("evt-1", _v(1), "poedhn", date(2026, 9, 4),
                 ["Διαδήλωση/Πορεία/Συγκέντρωση"], 40.640, 22.944, False)]
    match = find_announced_duplicate(
        centroid=_v(-1), event_day=date(2026, 9, 4),
        action_forms=["Διαδήλωση/Πορεία/Συγκέντρωση"],
        place_lat=40.640, place_lon=22.944, is_national=False,
        existing=existing, sim_threshold=0.9,
    )
    assert match == "evt-1"


def test_no_merge_same_day_action_but_different_city():
    existing = [("evt-1", _v(1), "poedhn", date(2026, 9, 4),
                 ["Διαδήλωση/Πορεία/Συγκέντρωση"], 40.640, 22.944, False)]  # Thessaloniki
    match = find_announced_duplicate(
        centroid=_v(-1), event_day=date(2026, 9, 4),
        action_forms=["Διαδήλωση/Πορεία/Συγκέντρωση"],
        place_lat=37.983, place_lon=23.727, is_national=False,  # Athens
        existing=existing, sim_threshold=0.9,
    )
    assert match is None


def test_merge_on_high_centroid_sim_alone():
    existing = [("evt-1", _v(1), "adedy", date(2026, 9, 5),
                 ["Απεργία/Στάση εργασίας"], None, None, False)]
    match = find_announced_duplicate(
        centroid=_v(1), event_day=date(2026, 10, 1),
        action_forms=["Κατάληψη"], place_lat=None, place_lon=None, is_national=False,
        existing=existing, sim_threshold=0.95,
    )
    assert match == "evt-1"


def test_dateless_joiner_matches_on_place_and_action():
    # A backing union restates the place (ΔΕΘ/Θεσσαλονίκη) + action but NOT the date.
    existing = [("evt-1", _v(1), "pame", date(2026, 9, 5),
                 ["Διαδήλωση/Πορεία/Συγκέντρωση"], 40.640, 22.944, False)]
    match = find_announced_duplicate(
        centroid=_v(-1), event_day=None,
        action_forms=["Διαδήλωση/Πορεία/Συγκέντρωση"],
        place_lat=40.640, place_lon=22.944, is_national=False,
        existing=existing, sim_threshold=0.9,
    )
    assert match == "evt-1"


def test_dateless_placeless_does_not_match():
    # No date AND no place/national → nothing to anchor on → only centroid could match.
    existing = [("evt-1", _v(1), "pame", date(2026, 9, 5),
                 ["Διαδήλωση/Πορεία/Συγκέντρωση"], 40.640, 22.944, False)]
    match = find_announced_duplicate(
        centroid=_v(-1), event_day=None,
        action_forms=["Διαδήλωση/Πορεία/Συγκέντρωση"],
        place_lat=None, place_lon=None, is_national=False,
        existing=existing, sim_threshold=0.9,
    )
    assert match is None
