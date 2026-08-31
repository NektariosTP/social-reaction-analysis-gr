# tests/reactions/test_actions.py
from reactions.actions import map_action_forms
from enrich.classify import AXIS_ACTION_FORMS


def test_strike_maps_to_apergia():
    forms = map_action_forms("Τετράωρη στάση εργασίας στον ΔΕΔΔΗΕ")
    assert "Απεργία/Στάση εργασίας" in forms
    assert set(forms) <= set(AXIS_ACTION_FORMS)


def test_rally_maps_to_diadilosi():
    assert "Διαδήλωση/Πορεία/Συγκέντρωση" in map_action_forms("Πανελλαδικό Συλλαλητήριο και πορεία")


def test_multi_label():
    forms = map_action_forms("Απεργία και συγκέντρωση")
    assert {"Απεργία/Στάση εργασίας", "Διαδήλωση/Πορεία/Συγκέντρωση"} <= set(forms)


def test_empty_when_none():
    assert map_action_forms("Ενημέρωση αιρετού") == []
