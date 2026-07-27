"""Tests for gold-eval metrics."""

from scripts.gold_common import binary_prf, multilabel_prf, pairwise_f1


def test_binary_prf():
    m = binary_prf(tp=8, fp=2, fn=2)
    assert round(m["precision"], 2) == 0.80
    assert round(m["recall"], 2) == 0.80
    assert round(m["f1"], 2) == 0.80


def test_binary_prf_zero_safe():
    m = binary_prf(tp=0, fp=0, fn=0)
    assert m["precision"] == 0.0 and m["recall"] == 0.0 and m["f1"] == 0.0


def test_pairwise_f1_perfect():
    labels = [0, 0, 1, 1, 2]
    m = pairwise_f1(labels, labels)
    assert m["f1"] == 1.0


def test_pairwise_f1_all_singletons_vs_one_cluster():
    m = pairwise_f1([0, 1, 2, 3], [0, 0, 0, 0])
    assert m["recall"] == 0.0  # no predicted co-member pairs


def test_multilabel_prf_micro():
    pred = [{"A", "B"}, {"C"}]
    gold = [{"A"}, {"C", "D"}]
    m = multilabel_prf(pred, gold)  # tp=2 (A,C), fp=1 (B), fn=1 (D)
    assert round(m["precision"], 3) == 0.667
    assert round(m["recall"], 3) == 0.667
