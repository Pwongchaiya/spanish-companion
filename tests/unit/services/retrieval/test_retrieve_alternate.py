"""Unit tests for HybridRetrievalOrchestrationService.retrieve(alternate=True) and LexicalStrategy.

The alternate (second-opinion) path: lexical search on the raw query text,
no embedding, no fusion, no configured (distance-based) filters; category
boost still applies. Default retrieve() behaviour is covered by
test_retrieve_logic.py and must not change.
"""

from unittest.mock import Mock

from rag.services.foundations.chunk_repository import IChunkRepositoryService
from rag.services.orchestrations.retrieval.strategies.filters import ResultFilter
from rag.services.orchestrations.retrieval.strategies.lexical import LexicalStrategy


class TestHybridRetrievalServiceRetrieveAlternate:

    def test_should_search_alternate_strategy_with_raw_text_and_skip_dense_pipeline(
        self, service_factory, mock_embedding_model, mock_strategy, mock_alternate_strategy, make_chunk
    ):
        # given
        mock_filter = Mock(spec=ResultFilter)
        service = service_factory(alternate_strategy=mock_alternate_strategy, filters=[mock_filter])
        mock_alternate_strategy.search_text.return_value = [make_chunk(4), make_chunk(5)]

        # when
        result = service.retrieve(query="ser vs estar", top_k=3, alternate=True)

        # then
        assert [c.chunk_id for c in result] == [4, 5]
        mock_alternate_strategy.search_text.assert_called_once_with("ser vs estar", 3)
        mock_embedding_model.embed.assert_not_called()
        mock_strategy.search.assert_not_called()
        mock_filter.apply.assert_not_called()

    def test_should_boost_category_and_slice_to_top_k_on_alternate_path(
        self, service_factory, mock_alternate_strategy, make_chunk
    ):
        # given
        service = service_factory(alternate_strategy=mock_alternate_strategy)
        mock_alternate_strategy.search_text.return_value = [
            make_chunk(1, topic="other"),
            make_chunk(2, topic="preterite"),
            make_chunk(3, topic="other"),
        ]

        # when
        result = service.retrieve(query="fui", top_k=2, category="preterite", alternate=True)

        # then
        assert [c.chunk_id for c in result] == [2, 1]
        mock_alternate_strategy.search_text.assert_called_once_with("fui", 2)

    def test_should_return_empty_when_no_alternate_strategy_configured(
        self, service, mock_embedding_model, mock_strategy
    ):
        # when
        result = service.retrieve(query="fui", top_k=3, alternate=True)

        # then
        assert result == []
        mock_embedding_model.embed.assert_not_called()
        mock_strategy.search.assert_not_called()

    def test_should_not_touch_alternate_strategy_on_default_retrieve(
        self, service_factory, mock_alternate_strategy, mock_strategy, make_chunk
    ):
        # given
        service = service_factory(alternate_strategy=mock_alternate_strategy)
        mock_strategy.search.return_value = [make_chunk(1)]

        # when
        service.retrieve(query="fui", top_k=3)

        # then
        mock_alternate_strategy.search_text.assert_not_called()
        mock_strategy.search.assert_called_once()


class TestLexicalStrategy:

    def test_should_delegate_to_chunk_repository_search_by_text(self, mock_logging_broker, make_chunk):
        # given
        repo = Mock(spec=IChunkRepositoryService)
        repo.search_by_text.return_value = [make_chunk(9)]
        strategy = LexicalStrategy(repo, logging_broker=mock_logging_broker)

        # when
        result = strategy.search_text("pretérito", 4)

        # then
        assert [c.chunk_id for c in result] == [9]
        repo.search_by_text.assert_called_once_with("pretérito", 4)
