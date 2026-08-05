"""Score the keyword relevance gate against tests/fixtures/gold/relevance.jsonl."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from ingestion.filters.relevance import SpacyRelevanceFilter  # noqa: E402
from scripts.gold_common import binary_prf, load_jsonl  # noqa: E402


def main() -> None:
    recs = load_jsonl(Path("tests/fixtures/gold/relevance.jsonl"))
    _KEYWORDS = Path("ingestion/filters/keywords.yml")
    flt = SpacyRelevanceFilter(keywords_path=_KEYWORDS)
    tp = fp = fn = tn = 0
    for r in recs:
        text = f"{r['title']} {r['body_excerpt']}"
        predicted_relevant = flt.is_relevant(text)
        gold_relevant = r["label"] == "relevant"
        if predicted_relevant and gold_relevant:
            tp += 1
        elif predicted_relevant and not gold_relevant:
            fp += 1
        elif not predicted_relevant and gold_relevant:
            fn += 1
        else:
            tn += 1
    m = binary_prf(tp, fp, fn)
    print(f"[relevance] n={len(recs)} tp={tp} fp={fp} fn={fn} tn={tn}")
    print(f"[relevance] precision={m['precision']:.3f} recall={m['recall']:.3f} f1={m['f1']:.3f}")


if __name__ == "__main__":
    main()
