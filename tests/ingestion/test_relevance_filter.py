"""Tests for SpacyRelevanceFilter."""
from pathlib import Path

import pytest

from ingestion.filters.relevance import SpacyRelevanceFilter

_KEYWORDS_PATH = Path(__file__).parent.parent.parent / "ingestion" / "filters" / "keywords.yml"


@pytest.fixture(scope="module")
def filter_sm() -> SpacyRelevanceFilter:
    return SpacyRelevanceFilter(keywords_path=_KEYWORDS_PATH, model="el_core_news_sm")


def test_passes_exact_keyword(filter_sm: SpacyRelevanceFilter) -> None:
    assert filter_sm.is_relevant("48ωρη απεργία στα νοσοκομεία") is True


def test_passes_inflected_form(filter_sm: SpacyRelevanceFilter) -> None:
    # "απεργιακής" is an inflection of "απεργιακός" — lemma match
    assert filter_sm.is_relevant("απεργιακής δράσης") is True


def test_passes_multi_word_keyword(filter_sm: SpacyRelevanceFilter) -> None:
    assert filter_sm.is_relevant("στάση εργασίας εκπαιδευτικών") is True


def test_rejects_unrelated_text(filter_sm: SpacyRelevanceFilter) -> None:
    assert filter_sm.is_relevant("καλός καιρός αναμένεται αύριο στη χώρα") is False


def test_rejects_empty_string(filter_sm: SpacyRelevanceFilter) -> None:
    assert filter_sm.is_relevant("") is False


def test_is_relevant_case_insensitive(filter_sm: SpacyRelevanceFilter) -> None:
    assert filter_sm.is_relevant("ΑΠΕΡΓΙΑ ΣΗΜΕΡΑ") is True


def test_passes_conflict_keyword(filter_sm: SpacyRelevanceFilter) -> None:
    assert filter_sm.is_relevant("εκτοξεύτηκαν δακρυγόνα στο κέντρο") is True
