"""Unit tests for HybridRetrievalService.retrieve() -- pipeline behaviour.

Covers the stage order the service owns:
    embed once -> every strategy -> fuse -> filters (+ per-call category
    boost) -> [:top_k]

See test_retrieve_validation.py for the blank-query / top_k guards.
"""

from unittest.mock import Mock

from rag.services.retrieval.strategies.filters import ResultFilter
from rag.services.retrieval.strategies.fusion import RankFusionStrategy


class TestHybridRetrievalServiceRetrieveLogic:

    def test_should_embed_query_once_and_pass_embedding_to_strategy(
        self, service, mock_embedding_model, mock_strategy, make_chunk, query_embedding
    ):
        # given
        mock_strategy.search.return_value = [make_chunk(1)]

        # when
        service.retrieve(query="ser vs estar", top_k=3)

        # then -- the query is embedded exactly once per call, and the
        # strategy receives that embedding rather than the raw text.
        mock_embedding_model.embed.assert_called_once_with(["ser vs estar"])
        mock_strategy.search.assert_called_once_with(query_embedding, 3)

    def test_should_return_fused_candidates_best_first(
        self, service, mock_strategy, make_chunk, query_embedding
    ):
        # given
        mock_strategy.search.return_value = [
            make_chunk(1, score=0.05),
            make_chunk(2, score=0.20),
            make_chunk(3, score=0.40),
        ]

        # when
        results = service.retrieve(query="ser vs estar", top_k=3)

        # then
        assert [result.chunk_id for result in results] == [1, 2, 3]
        mock_strategy.search.assert_called_once_with(query_embedding, 3)

    def test_should_slice_results_to_top_k(
        self, service, mock_strategy, make_chunk, query_embedding
    ):
        # given -- a strategy that over-returns (a lexical strategy legitimately
        # might); the service's own [:top_k] slice is the last word on length.
        mock_strategy.search.return_value = [make_chunk(1), make_chunk(2), make_chunk(3)]

        # when
        results = service.retrieve(query="ser vs estar", top_k=2)

        # then
        assert [result.chunk_id for result in results] == [1, 2]
        mock_strategy.search.assert_called_once_with(query_embedding, 2)

    def test_should_return_empty_list_when_corpus_has_no_match(
        self, service, mock_strategy, query_embedding
    ):
        # given -- empty is a valid result, not an error: Review short-circuits
        # on it before calling Generation.
        mock_strategy.search.return_value = []

        # when
        results = service.retrieve(query="ser vs estar", top_k=3)

        # then
        assert results == []
        mock_strategy.search.assert_called_once_with(query_embedding, 3)

    def test_should_never_call_chunk_repository_directly(
        self, service, mock_chunk_repository, mock_strategy, make_chunk
    ):
        # given -- chunk_repository is constructor-only: it exists to build the
        # default DenseVectorStrategy, which owns it. With `strategies`
        # overridden, nothing in the pipeline may touch it.
        mock_strategy.search.return_value = [make_chunk(1)]

        # when
        service.retrieve(query="ser vs estar", top_k=3)

        # then
        mock_chunk_repository.search_by_vector.assert_not_called()
        mock_chunk_repository.insert_chunk.assert_not_called()

    def test_should_pass_every_strategys_candidates_to_fusion(
        self, service_factory, mock_embedding_model, make_chunk, query_embedding
    ):
        # given -- two strategies, so fusion is provably a real merge stage and
        # not a one-list accident. PassThroughRankFusion refuses two lists by
        # design, so fusion is mocked here.
        first_strategy, second_strategy = Mock(), Mock()
        first_strategy.search.return_value = [make_chunk(1)]
        second_strategy.search.return_value = [make_chunk(2)]
        mock_fusion = Mock(spec=RankFusionStrategy)
        mock_fusion.fuse.return_value = [make_chunk(2), make_chunk(1)]
        service = service_factory(strategies=[first_strategy, second_strategy], fusion=mock_fusion)

        # when
        results = service.retrieve(query="ser vs estar", top_k=3)

        # then -- one embed for both strategies, and fusion's output is what
        # the caller gets (not either strategy's raw list).
        mock_embedding_model.embed.assert_called_once_with(["ser vs estar"])
        first_strategy.search.assert_called_once_with(query_embedding, 3)
        second_strategy.search.assert_called_once_with(query_embedding, 3)
        mock_fusion.fuse.assert_called_once_with([[make_chunk(1)], [make_chunk(2)]])
        assert [result.chunk_id for result in results] == [2, 1]

    def test_should_apply_configured_filters_to_fused_results(
        self, service_factory, mock_strategy, make_chunk
    ):
        # given
        mock_strategy.search.return_value = [make_chunk(1), make_chunk(2)]
        mock_filter = Mock(spec=ResultFilter)
        mock_filter.apply.return_value = [make_chunk(2), make_chunk(1)]
        service = service_factory(filters=[mock_filter])

        # when
        results = service.retrieve(query="ser vs estar", top_k=3)

        # then
        mock_filter.apply.assert_called_once_with([make_chunk(1), make_chunk(2)])
        assert [result.chunk_id for result in results] == [2, 1]

    def test_should_not_boost_by_category_when_category_is_none(
        self, service, mock_strategy, make_chunk, query_embedding
    ):
        # given -- chunk 2's topic would be floated to the front by a category
        # boost, so an unchanged order proves no boost filter ran.
        mock_strategy.search.return_value = [
            make_chunk(1, topic="vocabulary"),
            make_chunk(2, topic="ser-vs-estar"),
        ]

        # when
        results = service.retrieve(query="ella es feliz", top_k=3, category=None)

        # then
        assert [result.chunk_id for result in results] == [1, 2]
        mock_strategy.search.assert_called_once_with(query_embedding, 3)

    def test_should_boost_matching_topic_to_front_when_category_is_given(
        self, service, mock_strategy, make_chunk
    ):
        # given
        mock_strategy.search.return_value = [
            make_chunk(1, topic="vocabulary"),
            make_chunk(2, topic="ser-vs-estar"),
        ]

        # when
        results = service.retrieve(query="ella es feliz", top_k=3, category="ser vs estar")

        # then -- matching chunk floated, nothing dropped.
        assert [result.chunk_id for result in results] == [2, 1]

    def test_should_not_carry_category_boost_between_calls(
        self, service, mock_strategy, make_chunk
    ):
        # given -- the boost filter is built per call rather than appended to
        # the service's configured filters; a leak would make call two behave
        # like call one.
        mock_strategy.search.return_value = [
            make_chunk(1, topic="vocabulary"),
            make_chunk(2, topic="ser-vs-estar"),
        ]

        # when
        boosted = service.retrieve(query="ella es feliz", top_k=3, category="ser vs estar")
        unboosted = service.retrieve(query="ella es feliz", top_k=3)

        # then
        assert [result.chunk_id for result in boosted] == [2, 1]
        assert [result.chunk_id for result in unboosted] == [1, 2]
        assert mock_strategy.search.call_count == 2

    def test_should_apply_category_boost_after_configured_filters(
        self, service_factory, mock_strategy, make_chunk
    ):
        # given -- the per-call category hint gets the final say on order, so a
        # configured filter's ranking is what the boost partitions.
        mock_strategy.search.return_value = [
            make_chunk(1, topic="vocabulary"),
            make_chunk(2, topic="ser-vs-estar"),
        ]
        mock_filter = Mock(spec=ResultFilter)
        mock_filter.apply.return_value = [
            make_chunk(3, topic="vocabulary"),
            make_chunk(4, topic="ser-vs-estar"),
        ]
        service = service_factory(filters=[mock_filter])

        # when
        results = service.retrieve(query="ella es feliz", top_k=3, category="ser vs estar")

        # then -- the boost saw the configured filter's output, not the fused list.
        mock_filter.apply.assert_called_once_with(
            [make_chunk(1, topic="vocabulary"), make_chunk(2, topic="ser-vs-estar")]
        )
        assert [result.chunk_id for result in results] == [4, 3]
