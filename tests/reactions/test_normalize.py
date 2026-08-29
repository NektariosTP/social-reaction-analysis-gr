from reactions.normalize import clean_text


def test_strips_entities_and_tags():
    assert clean_text("ΟΧΙ &#8211; στην &#160;αποξήλωση <b>τώρα</b>") == "ΟΧΙ – στην αποξήλωση τώρα"


def test_drops_wordpress_tail_el():
    raw = "Απεργία 5 Σεπτέμβρη. Το άρθρο Απεργία εμφανίστηκε πρώτα στο ΑΔΕΔΥ."
    assert clean_text(raw) == "Απεργία 5 Σεπτέμβρη."


def test_drops_wordpress_tail_en():
    raw = "Strike notice. The post Strike appeared first on GENOP."
    assert clean_text(raw) == "Strike notice."


def test_drops_press_release_header():
    assert clean_text("ΔΕΛΤΙΟ ΤΥΠΟΥ Απεργία αύριο").strip() == "Απεργία αύριο"
