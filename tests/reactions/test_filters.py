from reactions.filters import passes_filter, FILTER_VARIANTS, ACTION_KEYWORDS_BROAD


def test_keeps_strike_notice():
    assert passes_filter("Τετράωρη στάση εργασίας στον ΔΕΔΔΗΕ Κρήτης")


def test_keeps_rally():
    assert passes_filter("Πανελλαδικό Συλλαλητήριο 5 Σεπτέμβρη στη Θεσσαλονίκη")


def test_drops_obituary():
    assert not passes_filter("Αποχαιρετάμε τον παλαίμαχο συνάδελφο")


def test_case_and_accent_insensitive():
    assert passes_filter("ΑΠΕΡΓΙΑ ΑΥΡΙΟ")


def test_variants_available():
    assert "broad" in FILTER_VARIANTS and "tight" in FILTER_VARIANTS
    assert FILTER_VARIANTS["broad"] == ACTION_KEYWORDS_BROAD
