"""Unit tests for CategoryBoostFilter and category_matches_topic.

Covers the flag-category -> corpus-topic matcher: word-boundary containment
on normalized strings, plus the alias table for pairs that share no word
even after normalization (see filters.py's category_matches_topic).
"""

from unittest.mock import Mock

import pytest

from rag.brokers.logging import LoggingBroker
from rag.services.orchestrations.retrieval.strategies.filters import CategoryBoostFilter, category_matches_topic
from tests.unit.services.retrieval.conftest import chunk


class TestCategoryMatchesTopic:

    @pytest.mark.parametrize(
        "topic, category",
        [
            ("ser-vs-estar", "ser vs estar"),
            ("preterite-vs-imperfect", "preterite vs imperfect"),
            ("subjunctive-basics", "subjunctive"),
            ("gender-agreement", "gender agreement"),
            # vs-stripping bridges this pair without an alias.
            ("por-vs-para", "por/para"),
            # alias table bridges these -- zero shared vocabulary otherwise.
            ("object-pronouns", "lo vs le"),
            ("object-pronouns", "le vs lo"),
            ("object-pronouns", "direct object pronoun"),
            ("object-pronouns", "indirect object pronoun"),
        ],
    )
    def test_should_match_known_category_topic_pairs(self, topic, category):
        assert category_matches_topic(topic, category) is True

    def test_should_not_match_a_category_no_topic_covers(self):
        assert category_matches_topic("gender-agreement", "vocabulary") is False


class TestCategoryBoostFilter:

    def test_should_pass_through_unchanged_when_no_category(self):
        # given
        chunks = [chunk(1, topic="ser-vs-estar"), chunk(2, topic="por-vs-para")]
        result_filter = CategoryBoostFilter(None, logging_broker=Mock(spec=LoggingBroker))

        # when
        result = result_filter.apply(chunks)

        # then
        assert result == chunks

    def test_should_boost_por_para_chunk_for_por_para_category(self):
        # given
        unrelated, por_para = chunk(1, topic="ser-vs-estar"), chunk(2, topic="por-vs-para")
        result_filter = CategoryBoostFilter("por/para", logging_broker=Mock(spec=LoggingBroker))

        # when
        result = result_filter.apply([unrelated, por_para])

        # then
        assert result == [por_para, unrelated]

    def test_should_boost_object_pronouns_chunk_for_lo_vs_le_category(self):
        # given
        unrelated, pronouns = chunk(1, topic="ser-vs-estar"), chunk(2, topic="object-pronouns")
        result_filter = CategoryBoostFilter("lo vs le", logging_broker=Mock(spec=LoggingBroker))

        # when
        result = result_filter.apply([unrelated, pronouns])

        # then
        assert result == [pronouns, unrelated]

    def test_should_leave_order_unchanged_when_category_matches_no_topic(self):
        # given
        chunks = [chunk(1, topic="ser-vs-estar"), chunk(2, topic="por-vs-para")]
        result_filter = CategoryBoostFilter("vocabulary", logging_broker=Mock(spec=LoggingBroker))

        # when
        result = result_filter.apply(chunks)

        # then -- no match anywhere, nothing dropped, fusion order kept.
        assert result == chunks
