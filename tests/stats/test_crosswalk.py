from stats.crosswalk import nuts2_to_name, name_to_nuts2, canonical_region_name


def test_all_13_peripheries_have_nuts2():
    m = nuts2_to_name()
    assert len(m) == 13
    assert m["EL30"] == "Attica"
    assert m["EL43"] == "Crete"


def test_name_to_nuts2_roundtrip():
    assert name_to_nuts2()["Central Macedonia"] == "EL52"


def test_canonical_from_greek_and_case():
    assert canonical_region_name("Αττική") == "Attica"
    assert canonical_region_name("attica") == "Attica"
    assert canonical_region_name("Attica") == "Attica"
    assert canonical_region_name("Nonsense") is None
    assert canonical_region_name(None) is None
