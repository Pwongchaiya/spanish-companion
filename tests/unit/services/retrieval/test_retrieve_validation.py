"""Unit tests for HybridRetrievalService.retrieve() -- input guards.

Both guards run before anything expensive: a rejected call must not embed the
query or hit a strategy, which is asserted on every case here rather than
just the raised type.

See test_retrieve_logic.py for the pipeline behaviour.
"""

import pytest


class TestHybridRetrievalServiceRetrieveValidation:

    @pytest.mark.parametrize("query", ["", "   ", "\t\n"])
    def test_should_raise_value_error_when_query_is_blank(
        self, service, mock_embedding_model, mock_strategy, query
    ):
        # when / then
        with pytest.raises(ValueError, match="query is required"):
            service.retrieve(query=query, top_k=3)

        mock_embedding_model.embed.assert_not_called()
        mock_strategy.search.assert_not_called()

    @pytest.mark.parametrize("top_k", [0, -1])
    def test_should_raise_value_error_when_top_k_is_below_one(
        self, service, mock_embedding_model, mock_strategy, top_k
    ):
        # when / then
        with pytest.raises(ValueError, match="top_k must be at least 1"):
            service.retrieve(query="ser vs estar", top_k=top_k)

        mock_embedding_model.embed.assert_not_called()
        mock_strategy.search.assert_not_called()

    def test_should_reject_blank_query_before_checking_top_k(
        self, service, mock_embedding_model, mock_strategy
    ):
        # given -- both guards fail; the query guard is first, so its message
        # is the one the caller sees.
        with pytest.raises(ValueError, match="query is required"):
            service.retrieve(query="", top_k=0)

        mock_embedding_model.embed.assert_not_called()
        mock_strategy.search.assert_not_called()
