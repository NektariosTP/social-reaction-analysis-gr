"""backfill_national: national-scope flag from stored article text."""
from __future__ import annotations

from scripts.backfill_national import _compute_is_national


def test_national_text_flagged_true() -> None:
    assert _compute_is_national("Πανελλαδική απεργία στο εμπόριο σε όλη τη χώρα") is True


def test_localized_text_flagged_false() -> None:
    assert _compute_is_national("Κατάληψη στο δημαρχείο Ηρακλείου") is False
