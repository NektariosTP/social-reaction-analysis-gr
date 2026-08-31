from scripts.eval_reaction_filter import score_variant

GOLD = [
    {"text": "Πανοικοδομική Απεργία 24 Ιούνη", "relevant": True},
    {"text": "Αποχαιρετάμε τον συνάδελφο", "relevant": False},
    {"text": "Συλλαλητήριο στη ΔΕΘ", "relevant": True},
]


def test_score_variant_perfect_broad():
    from reactions.filters import ACTION_KEYWORDS_BROAD
    s = score_variant(GOLD, ACTION_KEYWORDS_BROAD)
    assert s["tp"] == 2 and s["fp"] == 0 and s["fn"] == 0
    assert s["precision"] == 1.0 and s["recall"] == 1.0
