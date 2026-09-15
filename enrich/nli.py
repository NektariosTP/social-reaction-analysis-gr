"""NLI zero-shot primary classifier for the four-axis model + a noise gate.

Wraps MoritzLaurer/mDeBERTa-v3-base-mnli-xnli (transformers zero-shot-classification
pipeline) behind a lazily-loaded, cached seam so tests never download the ~1.5 GB
model — they patch _load_nli_pipeline directly.
"""
from __future__ import annotations

import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

NLI_MODEL = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"

# Calibrated in Step 10 via scripts/tune_noise_gate.py: best-precision point in the
# zero-false-negative band (0.30-0.55) — rejecting a real event outweighs the F1 cost
# of a few extra non-events reaching the detected triage queue.
NOISE_GATE_THRESHOLD = 0.55

_NOISE_GATE_TEMPLATE = "Αυτό το κείμενο περιγράφει {}."
_NOISE_GATE_LABELS = [
    "μια κοινωνική κινητοποίηση ή αντίδραση, όπως διαδήλωση, απεργία ή κατάληψη",
    "ειδήσεις άσχετες με κοινωνικές κινητοποιήσεις, όπως καιρός, αθλητισμός ή οικονομία",
]


@lru_cache(maxsize=1)
def _load_nli_pipeline():
    from transformers import pipeline
    from enrich.config import settings

    logger.info("[nli] Loading zero-shot model: %s", NLI_MODEL)
    return pipeline(
        "zero-shot-classification",
        model=NLI_MODEL,
        device=-1 if settings.embedding_device == "cpu" else 0,
    )


def classify_axis(
    text: str,
    labels: list[str],
    *,
    multi_label: bool,
    hypothesis_template: str,
) -> dict[str, float]:
    """Return label → entailment score for one axis, via the shared NLI pipeline."""
    clf = _load_nli_pipeline()
    out = clf(
        text,
        candidate_labels=labels,
        hypothesis_template=hypothesis_template,
        multi_label=multi_label,
    )
    return dict(zip(out["labels"], out["scores"]))


def noise_gate_score(text: str) -> float:
    """Return P(this text describes a genuine social-reaction event)."""
    clf = _load_nli_pipeline()
    out = clf(
        text,
        candidate_labels=_NOISE_GATE_LABELS,
        hypothesis_template=_NOISE_GATE_TEMPLATE,
        multi_label=False,
    )
    scores = dict(zip(out["labels"], out["scores"]))
    return scores[_NOISE_GATE_LABELS[0]]
