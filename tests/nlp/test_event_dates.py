from __future__ import annotations
from datetime import date, datetime, timezone
import pytest
from nlp.event_dates import resolve_event_day, EventDay

# 2026-09-14 is a Monday; "την Πέμπτη" → 2026-09-17, "την Τετάρτη" → 2026-09-16.
_MON = datetime(2026, 9, 14, 10, 0, tzinfo=timezone.utc)

def test_explicit_title_date_wins():
    r = resolve_event_day("ΑΔΕΔΥ: Στάση εργασίας στις 16 Σεπτεμβρίου", None, _MON)
    assert r == EventDay(day=date(2026, 9, 16), source="title")

def test_relative_weekday_in_title_resolved_against_pubdate():
    # The Cyprus block: "την Πέμπτη" with no calendar date → 17/9.
    r = resolve_event_day("Σε 24ωρη απεργία την Πέμπτη οι ωρομίσθιοι", None, _MON)
    assert r == EventDay(day=date(2026, 9, 17), source="weekday")

def test_deictic_simera_is_publish_day():
    r = resolve_event_day("Απεργούν σήμερα οι εργαζόμενοι", None, _MON)
    assert r == EventDay(day=date(2026, 9, 14), source="weekday")

def test_body_used_when_title_dateless():
    r = resolve_event_day("Στάση εργασίας των δικαστικών", "Η κινητοποίηση στις 16/9 στη Σύνταγμα", _MON)
    assert r == EventDay(day=date(2026, 9, 16), source="body")

def test_body_mode_breaks_multivalued():
    # 16/9 mentioned twice, 30/9 once → dominant is 16/9.
    r = resolve_event_day("Στάση", "16/9 ... 16 Σεπτεμβρίου ... και στις 30 Σεπτεμβρίου", _MON)
    assert r.day == date(2026, 9, 16)

def test_returns_none_when_no_date():
    assert resolve_event_day("ΠΑΜΕ: σχόλιο για τα ΜΜΕ", "χωρίς ημερομηνία", _MON) is None
