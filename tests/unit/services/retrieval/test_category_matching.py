"""Unit tests for filters._matches -- flag-category vs corpus-topic matching."""

import pytest

from rag.services.orchestrations.retrieval.strategies.filters import _matches, _normalize


@pytest.mark.parametrize(
    "topic, category",
    [
        ("ser-vs-estar", "ser vs estar"),
        ("subjunctive-basics", "subjunctive"),
        ("por-vs-para", "por vs para"),
        ("articles", "article"),
        ("articles", "articles"),
        ("object-pronouns", "object pronoun"),
        ("object-pronouns", "pronouns"),
    ],
)
def test_should_match_when_category_and_topic_overlap(topic, category):
    assert _matches(_normalize(topic), _normalize(category))


@pytest.mark.parametrize(
    "topic, category",
    [
        ("ser-vs-estar", "insert"),
        ("articles", "particle"),
        ("por-vs-para", "vocabulary"),
    ],
)
def test_should_not_match_when_words_differ(topic, category):
    assert not _matches(_normalize(topic), _normalize(category))
