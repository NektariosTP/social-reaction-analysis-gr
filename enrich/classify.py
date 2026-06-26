"""Four-axis multi-label event classification.

Primary path: embedding zero-shot (no LLM tokens).
Fallback: LLM via instructor + Pydantic structured output for low-confidence clusters.
"""
from __future__ import annotations

import logging
from functools import lru_cache

import numpy as np
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Axis definitions
# ---------------------------------------------------------------------------

AXIS_ACTION_FORMS = [
    "Διαδήλωση/Πορεία/Συγκέντρωση",
    "Απεργία/Στάση εργασίας",
    "Κατάληψη",
    "Αποκλεισμός/Μπλόκο",
    "Μποϊκοτάζ",
    "Διαδικτυακή εκστρατεία",
    "Whistleblowing",
    "Αποχή",
]

AXIS_THEMATIC_FIELDS = [
    "Εργασιακό",
    "Πολιτικό/Θεσμικό",
    "Οικονομικό",
    "Περιβαλλοντικό",
    "Δικαιώματα/Κοινωνικό",
    "Εκπαίδευση",
    "Αστυνομική Βία",
    "Άλλο",
]

AXIS_CHANNEL = [
    "Φυσικό (offline)",
    "Ψηφιακό (online)",
    "Υβριδικό",
]

AXIS_INTENSITY = [
    "Ειρηνική",
    "Διαταρακτική (μη βίαιη, παρεμποδιστική)",
    "Βίαιη/Συγκρουσιακή",
]

# Multi-label axes use a lower threshold (top-K or above sim threshold)
_MULTILABEL_THRESHOLD = 0.35
_MULTILABEL_MAX = 3
_CONFIDENCE_LOW = 0.45  # below this → use LLM fallback


class ClassificationResult(BaseModel):
    action_forms: list[str]
    thematic_fields: list[str]
    channel: str
    intensity: str
    confidence: dict[str, float]
    used_llm_fallback: bool = False


# ---------------------------------------------------------------------------
# Zero-shot implementation
# ---------------------------------------------------------------------------

def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


@lru_cache(maxsize=1)
def _get_axis_embeddings() -> dict[str, np.ndarray]:
    """Embed all axis labels once and cache. Key = label string, value = unit vector."""
    from sentence_transformers import SentenceTransformer
    from enrich.config import settings

    all_labels = AXIS_ACTION_FORMS + AXIS_THEMATIC_FIELDS + AXIS_CHANNEL + AXIS_INTENSITY
    model = SentenceTransformer(settings.embedding_model)
    vecs: np.ndarray = model.encode(all_labels, normalize_embeddings=True)
    return {label: vec for label, vec in zip(all_labels, vecs)}


def classify_zero_shot(centroid: np.ndarray) -> ClassificationResult:
    """Classify a cluster centroid against all four axes without LLM calls."""
    label_embs = _get_axis_embeddings()

    def _top_single(axis_labels: list[str]) -> tuple[str, float]:
        sims = {lbl: _cosine_sim(centroid, label_embs[lbl]) for lbl in axis_labels}
        best = max(sims, key=sims.__getitem__)
        return best, sims[best]

    def _top_multi(axis_labels: list[str]) -> tuple[list[str], float]:
        sims = sorted(
            [(lbl, _cosine_sim(centroid, label_embs[lbl])) for lbl in axis_labels],
            key=lambda t: t[1],
            reverse=True,
        )
        selected = [lbl for lbl, s in sims if s >= _MULTILABEL_THRESHOLD][:_MULTILABEL_MAX]
        if not selected:
            selected = [sims[0][0]]
        return selected, sims[0][1]

    action_forms, action_conf = _top_multi(AXIS_ACTION_FORMS)
    thematic_fields, thematic_conf = _top_multi(AXIS_THEMATIC_FIELDS)
    channel, channel_conf = _top_single(AXIS_CHANNEL)
    intensity, intensity_conf = _top_single(AXIS_INTENSITY)

    return ClassificationResult(
        action_forms=action_forms,
        thematic_fields=thematic_fields,
        channel=channel,
        intensity=intensity,
        confidence={
            "action_forms": action_conf,
            "thematic_fields": thematic_conf,
            "channel": channel_conf,
            "intensity": intensity_conf,
        },
        used_llm_fallback=False,
    )


# ---------------------------------------------------------------------------
# LLM fallback (for low-confidence clusters)
# ---------------------------------------------------------------------------

class _LlmClassification(BaseModel):
    action_forms: list[str]
    thematic_fields: list[str]
    channel: str
    intensity: str


def classify_with_llm_fallback(
    centroid: np.ndarray,
    article_titles: list[str],
) -> ClassificationResult:
    """
    Classify using zero-shot first; fall back to LLM when confidence is low.
    Cached by event content — never re-classifies the same centroid+titles.
    """
    result = classify_zero_shot(centroid)
    min_conf = min(result.confidence.values())

    if min_conf >= _CONFIDENCE_LOW:
        return result

    logger.info("[classify] Low confidence (%.3f) — using LLM fallback.", min_conf)
    try:
        from enrich.llm_client import get_llm_client_and_model
        client, model = get_llm_client_and_model()
        titles_text = "\n".join(f"- {t}" for t in article_titles[:10])
        prompt = (
            "Classify this Greek social reaction event across four axes.\n\n"
            f"Article titles:\n{titles_text}\n\n"
            "Axes:\n"
            f"  action_forms (multi-label, pick 1-3): {', '.join(AXIS_ACTION_FORMS)}\n"
            f"  thematic_fields (multi-label, pick 1-3): {', '.join(AXIS_THEMATIC_FIELDS)}\n"
            f"  channel (single): {', '.join(AXIS_CHANNEL)}\n"
            f"  intensity (single): {', '.join(AXIS_INTENSITY)}\n"
        )
        llm_result: _LlmClassification = client.chat.completions.create(
            response_model=_LlmClassification,
            messages=[{"role": "user", "content": prompt}],
        )
        return ClassificationResult(
            action_forms=llm_result.action_forms,
            thematic_fields=llm_result.thematic_fields,
            channel=llm_result.channel,
            intensity=llm_result.intensity,
            confidence=result.confidence,
            used_llm_fallback=True,
        )
    except Exception as exc:
        logger.warning("[classify] LLM fallback failed: %s — using zero-shot result.", exc)
        return result
