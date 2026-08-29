"""Keyword pre-filter for union reactions. Substring match, accent/case-insensitive."""
from __future__ import annotations

import unicodedata

# Spec's Phase-A keyword set (docs/union-reactions-spec.md §Event-matching step 1).
# "απεργ"/"διαμαρτυρ" are truncated to their shared root (not the full noun) so verb
# conjugations match too — e.g. "Απεργούμε"/"Διαμαρτυρόμαστε" are common in real union
# feed titles (confirmed against live genop/pame/adedy/poedhn/oikodomon feeds) and were
# silently dropped by the full-noun forms "απεργια"/"διαμαρτυρια".
ACTION_KEYWORDS_BROAD = [
    "απεργ", "σταση εργασιας", "συλλαλητηριο", "κινητοποιηση",
    "μπλοκο", "καταληψη", "πορεια", "διαμαρτυρ", "συγκεντρωση",
]
# Tighter set for lower-base-rate (tier-2) sources — validated in Phase C via the harness.
ACTION_KEYWORDS_TIGHT = [
    "απεργ", "σταση εργασιας", "συλλαλητηριο", "συγκεντρωση", "πορεια",
]
FILTER_VARIANTS: dict[str, list[str]] = {
    "broad": ACTION_KEYWORDS_BROAD,
    "tight": ACTION_KEYWORDS_TIGHT,
}


def _fold(s: str) -> str:
    """Lowercase + strip diacritics so 'ΑΠΕΡΓΙΑ' == 'απεργία'."""
    nfd = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def passes_filter(text: str, keywords: list[str] | None = None) -> bool:
    kws = keywords if keywords is not None else ACTION_KEYWORDS_BROAD
    folded = _fold(text)
    return any(_fold(kw) in folded for kw in kws)
