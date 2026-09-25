"""Unit tests for ReviewOrchestrationService.explain_flag() -- Retrieval rejecting input.

H5 of the architecture conformance audit. Retrieval used to raise a bare
ValueError for a blank query or top_k < 1, which fell through to Review's
`except Exception` safety net as ReviewOrchestrationServiceException and so
surfaced over HTTP as a 500. It now raises
RetrievalOrchestrationValidationException, caught by name in Review's
validation tier, which the route maps to 400.

The wrapper is carried through whole rather than unwrapped, so from here the
RetrievalValidationError leaf sits at `.inner_exception.inner_exception` --
the same depth as Review's Foundation-tier leaves.
"""

import pytest

from api.models.orchestrations.review.exceptions import ReviewOrchestrationValidationException
from rag.models.orchestrations.retrieval.exceptions import (
    RetrievalOrchestrationValidationException,
    RetrievalValidationError,
)


class TestReviewOrchestratorExplainFlagRetrievalValidation:

    def test_should_raise_validation_exception_when_retrieval_rejects_the_query(
        self,
        service,
        mock_flag_service,
        mock_retrieval_service,
        mock_generation_service,
        mock_logging_broker,
        make_flag,
    ):
        # given
        mock_flag_service.get_flag.return_value = make_flag("flag-1")
        leaf = RetrievalValidationError("query is required")
        mock_retrieval_service.retrieve.side_effect = RetrievalOrchestrationValidationException(inner_exception=leaf)

        # when
        with pytest.raises(ReviewOrchestrationValidationException) as exc_info:
            service.explain_flag("flag-1")

        # then
        actual = exc_info.value
        assert isinstance(actual.inner_exception, RetrievalOrchestrationValidationException)
        assert actual.inner_exception.inner_exception is leaf

        mock_flag_service.get_flag.assert_called_once_with("flag-1")
        mock_retrieval_service.retrieve.assert_called_once()
        mock_generation_service.explain.assert_not_called()

        mock_logging_broker.log_error.assert_called_once()
        logged_exception = mock_logging_broker.log_error.call_args.args[0]
        assert type(logged_exception) is ReviewOrchestrationValidationException
