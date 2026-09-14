from scripts.eval_announcement_merge import evaluate


def test_day_gate_prevents_cross_day_false_positive():
    pairs = [
        {"a": "Αντιφασιστική συγκέντρωση 18 Σεπτέμβρη", "b": "Αντιφασιστική συγκέντρωση 18 Σεπτέμβρη",
         "day_a": "2026-09-16", "day_b": "2026-09-18", "same_event": False},
    ]
    # identical text (sim ~1.0) but different days → gate blocks it → no false positive
    m = evaluate(pairs, threshold=0.72, day_gate=True)
    assert m["fp"] == 0
