"""Per-axis multi-label P/R/F1 of the NLI classifier vs events.jsonl."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from enrich.classify import classify_nli  # noqa: E402
from scripts.gold_common import load_jsonl, multilabel_prf, normalize_label  # noqa: E402

AXES = ["action_forms", "thematic_fields", "channel", "intensity"]


def _to_set(v) -> set:
    if v is None:
        return set()
    items = v if isinstance(v, list) else [v]
    return {normalize_label(x) for x in items}


def main() -> None:
    recs = [r for r in load_jsonl(Path("tests/fixtures/gold/events.jsonl")) if r.get("is_event")]
    per_axis_pred: dict[str, list[set]] = {a: [] for a in AXES}
    per_axis_gold: dict[str, list[set]] = {a: [] for a in AXES}
    for r in recs:
        text = " ".join(r["article_titles"]) + " " + " ".join(r["article_bodies"])
        result = classify_nli(text)
        preds = {
            "action_forms": {normalize_label(x) for x in result.action_forms},
            "thematic_fields": {normalize_label(x) for x in result.thematic_fields},
            "channel": {normalize_label(result.channel)} if result.channel else set(),
            "intensity": {normalize_label(result.intensity)} if result.intensity else set(),
        }
        for a in AXES:
            per_axis_pred[a].append(preds[a])
            per_axis_gold[a].append(_to_set(r.get(a)))
    for a in AXES:
        m = multilabel_prf(per_axis_pred[a], per_axis_gold[a])
        print(f"[classify:{a}] P={m['precision']:.3f} R={m['recall']:.3f} F1={m['f1']:.3f}")


if __name__ == "__main__":
    main()