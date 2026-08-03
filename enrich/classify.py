"""Four-axis multi-label event classification.

Primary path: embedding zero-shot (no LLM tokens).
Fallback: LLM via instructor + Pydantic structured output for low-confidence clusters.
"""
from __future__ import annotations

import logging

from enrich.nli import classify_axis
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
# Calibrated in B1 step 11 via scripts/tune_multilabel_threshold.py: best (or
# tied-best) F1 for both action_forms and thematic_fields in the 0.20-0.50
# sweep — higher values (up to 0.99) score marginally better but are treated
# as overfit to the 23-event gold set, not adopted (see scorecard B1 note).
_MULTILABEL_THRESHOLD = 0.50
_MULTILABEL_MAX = 3
_CONFIDENCE_LOW = 0.45  # below this → use LLM fallback
_HYPOTHESIS_TEMPLATES = {
    "action_forms": "Αυτό το κείμενο περιγράφει τη μορφή δράσης: {}.",
    "thematic_fields": "Αυτό το κείμενο αφορά το θεματικό πεδίο: {}.",
    "channel": "Αυτή η δράση διεξήχθη μέσω: {}.",
    "intensity": "Η ένταση αυτής της δράσης είναι: {}.",
}

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

def classify_nli(text: str) -> ClassificationResult:
    """Classify event text against all four axes via NLI zero-shot (no LLM tokens)."""

    def _top_multi(axis_labels: list[str], axis_key: str) -> tuple[list[str], float]:
        scores = classify_axis(
            text, axis_labels, multi_label=True,
            hypothesis_template=_HYPOTHESIS_TEMPLATES[axis_key],
        )
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        selected = [lbl for lbl, s in ranked if s >= _MULTILABEL_THRESHOLD][:_MULTILABEL_MAX]
        if not selected:
            selected = [ranked[0][0]]
        return selected, ranked[0][1]

    def _top_single(axis_labels: list[str], axis_key: str) -> tuple[str, float]:
        scores = classify_axis(
            text, axis_labels, multi_label=False,
            hypothesis_template=_HYPOTHESIS_TEMPLATES[axis_key],
        )
        best = max(scores, key=scores.__getitem__)
        return best, scores[best]

    action_forms, action_conf = _top_multi(AXIS_ACTION_FORMS, "action_forms")
    thematic_fields, thematic_conf = _top_multi(AXIS_THEMATIC_FIELDS, "thematic_fields")
    channel, channel_conf = _top_single(AXIS_CHANNEL, "channel")
    intensity, intensity_conf = _top_single(AXIS_INTENSITY, "intensity")

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
    article_titles: list[str],
    article_bodies: list[str],
) -> ClassificationResult:
    """Classify using NLI first; fall back to LLM when confidence is low."""
    text = (" ".join(article_titles) + " " + " ".join(b[:500] for b in article_bodies)).strip()
    result = classify_nli(text)
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
        logger.warning("[classify] LLM fallback failed: %s — using NLI result.", exc)
        return result
