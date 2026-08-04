"""Score clustering against gold_group in tests/fixtures/gold/clustering.jsonl.

Baseline mode: use the pipeline_event_id already stored on each article as the
'predicted' grouping (what the current HDBSCAN+registry produced). Later
milestones re-run the new clusterer over the same fixture articles and compare."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from sklearn.metrics import adjusted_rand_score, v_measure_score  # noqa: E402

from nlp.config import settings  # noqa: E402
from scripts.gold_common import load_jsonl, pairwise_f1  # noqa: E402


def _single_pass_pred(recs: list[dict], tau: float) -> list[int]:
    from nlp.clustering import single_pass_cluster
    from nlp.embeddings import _load_model, embed_texts
    texts = [f"{r['title']} {r['body_excerpt']}" for r in recs]
    vecs = embed_texts(_load_model(), texts)
    return single_pass_cluster(vecs, tau)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--single-pass", 
        action="store_true", 
        help="Run single-pass clustering instead of using baseline IDs"
    )
    args = parser.parse_args()

    recs = load_jsonl(Path("tests/fixtures/gold/clustering.jsonl"))
    gold = [r["gold_group"] for r in recs]

    if args.single_pass:
        tau = settings.cluster_tau
        print(f"[clustering] Mode: Single-pass (τ={tau})")
        pred = _single_pass_pred(recs, tau)
    else:
        print("[clustering] Mode: Baseline (pipeline_event_id)")
        # map each distinct pipeline_event_id (incl. None→own singleton) to an int label
        seen: dict[str, int] = {}
        pred = []
        for i, r in enumerate(recs):
            key = r.get("pipeline_event_id") or f"__none_{i}"
            pred.append(seen.setdefault(key, len(seen)))

    print(f"[clustering] n={len(recs)} gold_groups={len(set(gold))} pred_groups={len(set(pred))}")
    print(f"[clustering] ARI={adjusted_rand_score(gold, pred):.3f} "
          f"V-measure={v_measure_score(gold, pred):.3f}")
    m = pairwise_f1(pred, gold)
    print(f"[clustering] pairwise P={m['precision']:.3f} R={m['recall']:.3f} F1={m['f1']:.3f}")


if __name__ == "__main__":
    main()
