"""Greek social-reaction relevance filter (spaCy lemma-based)."""
from __future__ import annotations

import unicodedata
from abc import ABC, abstractmethod
from pathlib import Path

import spacy
import yaml
from spacy.language import Language


def _fold(text: str) -> str:
    """Lowercase and strip combining diacritics for accent-insensitive matching.

    Greek uppercase letters lose their accent marks when lowercased by Python
    (e.g. "ΑΠΕΡΓΙΑ".lower() == "απεργια", not "απεργία"). NFD decomposition
    followed by Mn-category removal normalises both sides so comparisons are
    accent-insensitive without altering the original text seen by NLP.
    """
    return "".join(
        c
        for c in unicodedata.normalize("NFD", text.lower())
        if unicodedata.category(c) != "Mn"
    )


class RelevanceFilter(ABC):
    @abstractmethod
    def is_relevant(self, text: str) -> bool:
        """Return True if *text* contains at least one reaction keyword."""


class SpacyRelevanceFilter(RelevanceFilter):
    def __init__(self, keywords_path: Path, model: str = "el_core_news_md") -> None:
        self._nlp: Language = spacy.load(model, exclude=["parser", "ner", "senter"])
        keywords = self._load_keywords(keywords_path)
        self._keywords_norm: frozenset[str] = frozenset(_fold(k) for k in keywords)
        self._lemmas: frozenset[str] = self._lemmatize(keywords)

    @staticmethod
    def _load_keywords(path: Path) -> list[str]:
        raw: dict[str, list[str]] = yaml.safe_load(path.read_text(encoding="utf-8"))
        return [kw for group in raw.values() for kw in group]

    def _lemmatize(self, keywords: list[str]) -> frozenset[str]:
        lemmas: set[str] = set()
        for kw in keywords:
            for token in self._nlp(kw.lower()):
                if token.lemma_ and not token.is_space:
                    lemmas.add(token.lemma_.lower())
        return frozenset(lemmas)

    def is_relevant(self, text: str) -> bool:
        if not text or not text.strip():
            return False
        norm = _fold(text)
        if any(kw in norm for kw in self._keywords_norm):
            return True
        try:
            doc_lemmas = {t.lemma_.lower() for t in self._nlp(text) if not t.is_space}
            return bool(doc_lemmas & self._lemmas)
        except Exception:
            return any(kw in norm for kw in self._keywords_norm)
