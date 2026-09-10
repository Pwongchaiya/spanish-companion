"""Unit tests for MaxDistanceFilter.

Covers the fix for the "RAG explanation quality gap" pending item: chunks
past the configured distance ceiling must be dropped, not just deprioritized
(that's the whole difference from CategoryBoostFilter, which never drops).
"""

from unittest.mock import Mock

from rag.brokers.logging import LoggingBroker
from rag.services.orchestrations.retrieval.strategies.filters import MaxDistanceFilter
from tests.unit.services.retrieval.conftest import chunk


class TestMaxDistanceFilter:

    def test_should_keep_chunks_at_or_under_the_ceiling(self):
        # given
        chunks = [chunk(1, score=0.10), chunk(2, score=0.65)]
        result_filter = MaxDistanceFilter(0.65, logging_broker=Mock(spec=LoggingBroker))

        # when
        result = result_filter.apply(chunks)

        # then
        assert result == chunks

    def test_should_drop_chunks_past_the_ceiling(self):
        # given
        close, far = chunk(1, score=0.10), chunk(2, score=0.90)
        result_filter = MaxDistanceFilter(0.65, logging_broker=Mock(spec=LoggingBroker))

        # when
        result = result_filter.apply([close, far])

        # then
        assert result == [close]

    def test_should_return_empty_list_when_nothing_is_close_enough(self):
        # given
        chunks = [chunk(1, score=0.90), chunk(2, score=0.95)]
        result_filter = MaxDistanceFilter(0.65, logging_broker=Mock(spec=LoggingBroker))

        # when
        result = result_filter.apply(chunks)

        # then -- this is the fallback path this filter exists to trigger:
        # Review treats [] as "no corpus match", not an error.
        assert result == []

    def test_should_log_the_dropped_chunk_ids_only_when_something_is_dropped(self):
        # given
        mock_logging_broker = Mock(spec=LoggingBroker)
        result_filter = MaxDistanceFilter(0.65, logging_broker=mock_logging_broker)

        # when -- nothing dropped
        result_filter.apply([chunk(1, score=0.10)])
        # then
        mock_logging_broker.log_info.assert_not_called()

        # when -- something dropped
        result_filter.apply([chunk(2, score=0.90)])
        # then
        mock_logging_broker.log_info.assert_called_once()
