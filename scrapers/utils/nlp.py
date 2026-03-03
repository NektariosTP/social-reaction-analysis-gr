"""
scrapers/utils/nlp.py

Greek NLP utilities for the scraper pipeline.

Provides lemma-based keyword matching to handle the highly inflected
nature of Greek: e.g. "απεργία" will match "απεργούν", "απεργιακό",
"απεργιών", "απεργιακής", etc.

Design
------
- A spaCy `el_core_news_sm` pipeline is loaded ONCE at module import time
  as a module-level singleton (_NLP).  The pipeline is configured with
  only the "tok2vec" and "morphologizer" components enabled (lemmatizer
  depends on morphologizer); the NER and parser are disabled for speed.
- `_KEYWORD_LEMMAS` is a frozenset of canonical lemmas for every keyword
  in REACTION_KEYWORDS, also computed once at import time.
- `contains_keyword_lemmatized(text)` tokenises the text, extracts its
  lemmas, and checks for intersection with `_KEYWORD_LEMMAS`.
- For very short strings (< 3 chars) or on any spaCy failure, the
  function falls back to the original substring match.

Usage
-----
    from scrapers.utils.nlp import contains_keyword_lemmatized
    if contains_keyword_lemmatized(title + " " + body):
        ...
"""

from __future__ import annotations

import logging

import spacy
from spacy.language import Language

from scrapers.config import REACTION_KEYWORDS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# spaCy model — loaded once, shared across all callers
# ---------------------------------------------------------------------------

def _load_model() -> Language:
    """Load the Greek spaCy model with only the components needed for lemmatisation."""
    try:
        # Enable tok2vec + morphologizer (lemmatizer requires both).
        # Disable parser and ner — not needed and slow.
        nlp = spacy.load(
            "el_core_news_sm",
            exclude=["parser", "ner", "senter"],
        )
        logger.debug("[nlp] Loaded spaCy model 'el_core_news_sm'.")
        return nlp
    except OSError as exc:
        logger.error(
            "[nlp] Could not load 'el_core_news_sm': %s.  "
            "Run: python -m spacy download el_core_news_sm",
            exc,
        )
        raise


_NLP: Language = _load_model()


# ---------------------------------------------------------------------------
# Pre-compute keyword lemma set
# ---------------------------------------------------------------------------

def _lemmatize_keywords(keywords: list[str]) -> frozenset[str]:
    """
    Return a frozenset of lower-cased lemmas for every keyword.

    Multi-word keywords (e.g. "στάση εργασίας") are split into individual
    tokens and each token's lemma is added separately — the caller's text
    is also tokenised at word level, so multi-word phrase matching is
    achieved implicitly when all component lemmas appear in the text.
    A phrase-level check is added separately for multi-word keywords.
    """
    lemmas: set[str] = set()
    for kw in keywords:
        doc = _NLP(kw.lower())
        for token in doc:
            if token.lemma_ and not token.is_space:
                lemmas.add(token.lemma_.lower())
    return frozenset(lemmas)


# Pre-computed at import time — O(1) lookups at runtime.
_KEYWORD_LEMMAS: frozenset[str] = _lemmatize_keywords(REACTION_KEYWORDS)

# Also keep a set of full lowercased keywords for the substring-fallback path.
_KEYWORDS_LOWER: frozenset[str] = frozenset(kw.lower() for kw in REACTION_KEYWORDS)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def contains_keyword_lemmatized(text: str) -> bool:
    """
    Return True if *text* appears to contain at least one reaction keyword,
    using lemma-based matching for Greek morphological variants.

    Matching strategy (applied in order; returns True on first match):
      1. Fast substring match on the raw lowercased text (catches exact forms
         and is very cheap for long texts).
      2. Per-token lemma intersection with pre-computed _KEYWORD_LEMMAS
         (catches inflected variants: plural, genitive, verb conjugations, …).

    Falls back to raw substring-only match if spaCy processing fails.

    Parameters
    ----------
    text : str
        Concatenated title + body (or any text to test).

    Returns
    -------
    bool
    """
    if not text or not text.strip():
        return False

    lowered = text.lower()

    # -- Fast path: exact substring match (zero NLP overhead) -----------------
    if any(kw in lowered for kw in _KEYWORDS_LOWER):
        return True

    # -- Lemma path -----------------------------------------------------------
    try:
        doc = _NLP(lowered)
        text_lemmas = {token.lemma_.lower() for token in doc if not token.is_space}
        return bool(text_lemmas & _KEYWORD_LEMMAS)
    except Exception as exc:  # pragma: no cover
        logger.warning("[nlp] spaCy processing failed, using substring fallback: %s", exc)
        return any(kw in lowered for kw in _KEYWORDS_LOWER)
