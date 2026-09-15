from datetime import date, datetime
from zoneinfo import ZoneInfo
from reactions.dates import extract_event_datetime, all_event_days

ATH = ZoneInfo("Europe/Athens")
NOW = datetime(2026, 8, 27, 12, 0, tzinfo=ATH)


def test_numeric_ddmmyyyy():
    d = extract_event_datetime("Παρασκευή 04/09/2026 Πανελλαδική Συγκέντρωση", now=NOW)
    assert d and d.when.date() == datetime(2026, 9, 4).date()
    assert d.is_future is True


def test_demotic_month():
    d = extract_event_datetime("Πανελλαδική Πανοικοδομική Απεργία 24 Ιούνη 2026", now=NOW)
    assert d and (d.when.month, d.when.day) == (6, 24)


def test_formal_month_no_year_rolls_forward():
    # 20 Ιουλίου already past on 27 Aug 2026 → rolls to 2027.
    d = extract_event_datetime("συγκέντρωση 20 Ιουλίου", now=NOW)
    assert d and d.when.year == 2027 and d.is_future is True


def test_time_of_day_parsed():
    d = extract_event_datetime("Συγκέντρωση 4/9/2026 στις 8:30", now=NOW)
    assert d and d.has_time and d.when.hour == 8 and d.when.minute == 30


def test_no_date_returns_none():
    assert extract_event_datetime("Αποχαιρετάμε τον συνάδελφο", now=NOW) is None


def test_dateless_time_defaults_to_midday():
    now = datetime(2026, 9, 14, 9, 0, tzinfo=ATH)
    got = extract_event_datetime("Συγκέντρωση στις 16 Σεπτεμβρίου", now=now)
    assert got is not None
    assert (got.when.hour, got.when.minute) == (12, 0)
    assert got.has_time is False


def test_explicit_time_is_preserved():
    now = datetime(2026, 9, 14, 9, 0, tzinfo=ATH)
    got = extract_event_datetime("Συγκέντρωση 16 Σεπτεμβρίου στις 18:30", now=now)
    assert got is not None
    assert (got.when.hour, got.when.minute) == (18, 30)
    assert got.has_time is True


def test_all_event_days_numeric_and_word():
    now = datetime(2026, 9, 14, 9, 0, tzinfo=ZoneInfo("Europe/Athens"))
    got = all_event_days("Απεργία 16/9 και στις 30 Σεπτεμβρίου", now=now)
    assert got == [date(2026, 9, 16), date(2026, 9, 30)]


def test_all_event_days_keeps_multiplicity():
    now = datetime(2026, 9, 14, 9, 0, tzinfo=ZoneInfo("Europe/Athens"))
    got = all_event_days("16 Σεπτεμβρίου ... πάλι 16/9", now=now)
    assert got == [date(2026, 9, 16), date(2026, 9, 16)]


def test_all_event_days_empty_when_no_date():
    assert all_event_days("Στάση εργασίας την Τετάρτη") == []
