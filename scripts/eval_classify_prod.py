"""Score the production LLM classifier against human-curated events (ground truth).

Unlike ``eval_classify.py`` (which scores against the small, in-sample gold
fixture), this reads a JSONL export of *curated production events* — where the
curator either approved the LLM output or corrected it, so the stored axis
labels are human-verified truth — re-runs ``enrich_event_llm`` on each event's
source articles, and reports per-axis P/R/F1 averaged over N runs. Because the
hosted LLM is non-deterministic, the spread across runs is reported too, which
turns that non-determinism into a measured reliability property.

Export the input with ``scripts/sql/export_curated.sql`` (see that file), then:

    uv run python -m scripts.eval_classify_prod <export.jsonl> [runs]

``runs`` defaults to 3.
"""
from __future__ import annotations

import os
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from enrich.enrich_llm import enrich_event_llm  # noqa: E402
from scripts.gold_common import load_jsonl, multilabel_prf, normalize_label  # noqa: E402

AXES = ["action_forms", "thematic_fields", "channel", "intensity"]
# Seconds between calls to stay under the hosted free-tier RPM/TPM limits
# (Groq free tier is ~8000 TPM and each call requests ~4000 tokens, so ~2/min).
_DELAY = float(os.environ.get("EVAL_DELAY", "4"))
# On a rate-limited (None) result, wait this long and retry once.
_RETRY_WAIT = float(os.environ.get("EVAL_RETRY_WAIT", "35"))


def _classify(r: dict):
    for attempt in (1, 2):
        result = enrich_event_llm(
            article_titles=r["article_titles"],
            article_bodies=r["article_bodies"],
            n_sources=len(r["article_titles"]),
            reference_date=r.get("published_at"),
        )
        if result is not None or attempt == 2:
            return result
        time.sleep(_RETRY_WAIT)
    return None


def _to_set(v) -> set:
    if v is None:
        return set()
    items = v if isinstance(v, list) else [v]
    return {normalize_label(x) for x in items if x}


def _score_once(recs: list[dict]) -> tuple[dict[str, dict[str, float]], int, int]:
    pred: dict[str, list[set]] = {a: [] for a in AXES}
    gold: dict[str, list[set]] = {a: [] for a in AXES}
    ok = fail = 0
    for i, r in enumerate(recs):
        if i:
            time.sleep(_DELAY)
        result = _classify(r)
        if result is None:
            fail += 1
            continue
        ok += 1
        preds = {
            "action_forms": {normalize_label(x) for x in result.action_forms},
            "thematic_fields": {normalize_label(x) for x in result.thematic_fields},
            "channel": {normalize_label(result.channel)} if result.channel else set(),
            "intensity": {normalize_label(result.intensity)} if result.intensity else set(),
        }
        for a in AXES:
            pred[a].append(preds[a])
            gold[a].append(_to_set(r.get(a)))
    return {a: multilabel_prf(pred[a], gold[a]) for a in AXES}, ok, fail


def _fmt(xs: list[float]) -> str:
    mean = statistics.mean(xs)
    spread = statistics.pstdev(xs) if len(xs) > 1 else 0.0
    return f"{mean:.3f}±{spread:.3f}"


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: eval_classify_prod <export.jsonl> [runs]", file=sys.stderr)
        raise SystemExit(2)
    path = Path(sys.argv[1])
    runs = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    recs = [r for r in load_jsonl(path) if r.get("is_event", True)]
    print(f"[eval_classify_prod] {len(recs)} curated events x {runs} runs "
          f"(delay {_DELAY}s/call)\n")
    per_run = []
    for run in range(runs):
        scores, ok, fail = _score_once(recs)
        per_run.append(scores)
        print(f"  run {run + 1}: {ok} ok / {fail} failed")
        if run < runs - 1:
            time.sleep(_DELAY)
    print()
    for a in AXES:
        ps = [pr[a]["precision"] for pr in per_run]
        rs = [pr[a]["recall"] for pr in per_run]
        f1s = [pr[a]["f1"] for pr in per_run]
        print(f"[{a:16}] P={_fmt(ps)}  R={_fmt(rs)}  F1={_fmt(f1s)}")


if __name__ == "__main__":
    main()
