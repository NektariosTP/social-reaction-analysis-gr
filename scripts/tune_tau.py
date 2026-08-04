"""Sweep the single-pass cosine threshold τ against tests/fixtures/gold/clustering.jsonl
and report the operating point that maximizes pairwise-F1. Do NOT hardcode τ elsewhere;
copy the winner into nlp/config.py cluster_tau and the scorecard."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
from nlp.clustering import single_pass_cluster  # noqa: E402
from nlp.embeddings import _load_model, embed_texts  # noqa: E402
from scripts.gold_common import load_jsonl, pairwise_f1  # noqa: E402


def main() -> None:
    recs = load_jsonl(Path("tests/fixtures/gold/clustering.jsonl"))
    gold = [r["gold_group"] for r in recs]
    texts = [f"{r['title']} {r['body_excerpt']}" for r in recs]
    model = _load_model()
    vecs = embed_texts(model, texts)

    best = (0.0, -1.0)  # (tau, f1)
    for tau in [round(0.70 + 0.02 * i, 2) for i in range(11)]:  # 0.70..0.90
        pred = single_pass_cluster(vecs, tau)
        m = pairwise_f1(pred, gold)
        print(f"tau={tau:.2f}  pairwise_F1={m['f1']:.3f}  P={m['precision']:.3f}  R={m['recall']:.3f}  groups={len(set(pred))}")
        if m["f1"] > best[1]:
            best = (tau, m["f1"])
    print(f"\nBEST tau={best[0]:.2f} pairwise_F1={best[1]:.3f}  → set nlp/config.py cluster_tau")


if __name__ == "__main__":
    main()
