"""Unit tests for HybridRetrievalOrchestrationService.retrieve() -- input guards.

Both guards run before anything expensive: a rejected call must not embed the
query or hit a strategy, which is asserted on every case here rather than
just the raised type.

The guards used to raise a bare ValueError from outside _try_catch. H5 of the
architecture conformance audit replaced that with the RetrievalValidationError
leaf, wrapped and logged as RetrievalOrchestrationValidationException like
every other failure this service produces -- so each case also asserts the
wrapper, the leaf inside it, and the single log_error call.

See test_retrieve_logic.py for the pipeline behaviour.
"""

import pytest

from rag.models.orchestrations.retrieval.exceptions import (
    RetrievalOrchestrationValidationException,
    RetrievalValidationError,
)


class TestHybridRetrievalServiceRetrieveValidation:

    @pytest.mark.parametrize("query", ["", "   ", "\t\n"])
    def test_should_raise_validation_exception_when_query_is_blank(
        self, service, mock_embedding_model, mock_strategy, mock_logging_broker, query
    ):
        # when / then
        with pytest.raises(RetrievalOrchestrationValidationException) as exc_info:
            service.retrieve(query=query, top_k=3)

        actual = exc_info.value
        assert isinstance(actual.inner_exception, RetrievalValidationError)
        assert actual.inner_exception.args == ("query is required",)

        mock_embedding_model.embed.assert_not_called()
        mock_strategy.search.assert_not_called()

        mock_logging_broker.log_error.assert_called_once()
        logged_exception = mock_logging_broker.log_error.call_args.args[0]
        assert type(logged_exception) is RetrievalOrchestrationValidationException

    @pytest.mark.parametrize("top_k", [0, -1])
    def test_should_raise_validation_exception_when_top_k_is_below_one(
        self, service, mock_embedding_model, mock_strategy, mock_logging_broker, top_k
    ):
        # when / then
        with pytest.raises(RetrievalOrchestrationValidationException) as exc_info:
            service.retrieve(query="ser vs estar", top_k=top_k)

        actual = exc_info.value
        assert isinstance(actual.inner_exception, RetrievalValidationError)
        assert actual.inner_exception.args == (f"top_k must be at least 1, got {top_k}",)

        mock_embedding_model.embed.assert_not_called()
        mock_strategy.search.assert_not_called()

        mock_logging_broker.log_error.assert_called_once()

    def test_should_reject_blank_query_before_checking_top_k(self, service, mock_embedding_model, mock_strategy):
        # given -- both guards fail; the query guard is first, so its message
        # is the one the caller sees.
        with pytest.raises(RetrievalOrchestrationValidationException) as exc_info:
            service.retrieve(query="", top_k=0)

        assert exc_info.value.inner_exception.args == ("query is required",)

        mock_embedding_model.embed.assert_not_called()
        mock_strategy.search.assert_not_called()
