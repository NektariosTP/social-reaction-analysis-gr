# reactions/actions.py
"""Map filter keywords → Axis-1 action-form labels (verbatim from enrich.axes)."""
from __future__ import annotations

import unicodedata

from enrich.axes import AXIS_ACTION_FORMS

# keyword-root (folded) → exact AXIS_ACTION_FORMS label
_MAP: list[tuple[str, str]] = [
    ("απεργ", "Απεργία/Στάση εργασίας"),
    ("σταση εργασιας", "Απεργία/Στάση εργασίας"),
    ("συλλαλητηρ", "Διαδήλωση/Πορεία/Συγκέντρωση"),
    ("συγκεντρωσ", "Διαδήλωση/Πορεία/Συγκέντρωση"),
    ("πορεια", "Διαδήλωση/Πορεία/Συγκέντρωση"),
    ("διαδηλωσ", "Διαδήλωση/Πορεία/Συγκέντρωση"),
    ("διαμαρτυρ", "Διαδήλωση/Πορεία/Συγκέντρωση"),
    ("κινητοποιησ", "Διαδήλωση/Πορεία/Συγκέντρωση"),
    ("καταληψ", "Κατάληψη"),
    ("μπλοκο", "Αποκλεισμός/Μπλόκο"),
    ("αποκλεισμ", "Αποκλεισμός/Μπλόκο"),
    ("αποχη", "Αποχή"),
]

assert {label for _, label in _MAP} <= set(AXIS_ACTION_FORMS)  # guard: labels stay in sync


def _fold(s: str) -> str:
    nfd = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def map_action_forms(text: str) -> list[str]:
    folded = _fold(text)
    out: list[str] = []
    for root, label in _MAP:
        if root in folded and label not in out:
            out.append(label)
    return out
