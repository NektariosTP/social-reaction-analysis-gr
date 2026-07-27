"""Tests for gold-eval metrics."""
from scripts.gold_common import binary_prf


def test_binary_prf():
    m = binary_prf(tp=8, fp=2, fn=2)
    assert round(m["precision"], 2) == 0.80
    assert round(m["recall"], 2) == 0.80
    assert round(m["f1"], 2) == 0.80


def test_binary_prf_zero_safe():
    m = binary_prf(tp=0, fp=0, fn=0)
    assert m["precision"] == 0.0 and m["recall"] == 0.0 and m["f1"] == 0.0
