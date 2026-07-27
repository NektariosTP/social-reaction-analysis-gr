"""Per-axis multi-label P/R/F1 of the current classifier vs events.jsonl.

Embeds each event's labeled text, runs classify_zero_shot on the centroid,
compares predicted axis label-sets to the gold axis labels.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
from enrich.classify import classify_zero_shot  # noqa: E402
from nlp.embeddings import _load_model  # noqa: E402
from scripts.gold_common import load_jsonl, multilabel_prf  # noqa: E402

AXES = ["action_forms", "thematic_fields", "channel", "intensity"]


def _to_set(v) -> set:
    if v is None:
        return set()
    return set(v) if isinstance(v, list) else {v}


def main() -> None:
    recs = [r for r in load_jsonl(
        Path("tests/fixtures/gold/events.jsonl")) if r.get("is_event")]
    per_axis_pred: dict[str, list[set]] = {a: [] for a in AXES}
    per_axis_gold: dict[str, list[set]] = {a: [] for a in AXES}
    model = _load_model()
    for r in recs:
        text = " ".join(r["article_titles"]) + " " + " ".join(r["article_bodies"])
        centroid = np.asarray(
            model.encode([text], normalize_embeddings=True)[0],
            dtype=np.float32)
        result = classify_zero_shot(centroid)  # ClassificationResult
        preds = {
            "action_forms": set(result.action_forms),
            "thematic_fields": set(result.thematic_fields),
            "channel": {result.channel} if result.channel else set(),
            "intensity": {result.intensity} if result.intensity else set(),
        }
        for a in AXES:
            per_axis_pred[a].append(preds[a])
            per_axis_gold[a].append(_to_set(r.get(a)))
    for a in AXES:
        m = multilabel_prf(per_axis_pred[a], per_axis_gold[a])
        print(f"[classify:{a}] P={m['precision']:.3f} R={m['recall']:.3f} "
              f"F1={m['f1']:.3f}")


if __name__ == "__main__":
    main()
