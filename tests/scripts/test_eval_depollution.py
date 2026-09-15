import json
from pathlib import Path
from scripts.eval_depollution import evaluate

_FIX = Path(__file__).parent.parent / "nlp" / "fixtures" / "depollution_c4f30e75.jsonl"

def _rows():
    return [json.loads(l) for l in _FIX.read_text(encoding="utf-8").splitlines() if l.strip()]

def test_cyprus_block_peels_and_no_article_in_two_groups():
    m = evaluate(_rows(), min_bucket=3, tolerance_days=0)
    assert m["cyprus_peeled"] is True          # 17/9 separated from 16/9 primary
    assert m["cross_group_articles"] == 0       # invariant: no id under two groups
    assert m["n_groups"] >= 2
