"""Unit tests for ReviewOrchestrationService.explain_flag() -- unknown flag_id.

The lookup happens before any retrieval or generation work, so an unknown id
must cost nothing downstream.

The id is now rejected by FlagService, which raises FlagValidationException
wrapping NotFoundFlagException. Review re-wraps that whole exception rather
than unwrapping it, so the leaf sits at `.inner_exception.inner_exception`.
Whether the list was empty or merely lacked the id is no longer visible from
here -- that distinction belongs to FlagService's own tier.
"""

import pytest

from api.models.foundations.flag.exceptions import FlagValidationException, NotFoundFlagException
from api.models.orchestrations.review.exceptions import ReviewOrchestrationValidationException


class TestReviewOrchestratorExplainFlagExceptions:

    def test_should_raise_validation_exception_before_retrieval_when_flag_id_is_unknown(
        self,
        service,
        mock_flag_service,
        mock_retrieval_service,
        mock_generation_service,
    ):
        # given
        leaf = NotFoundFlagException("does-not-exist")
        mock_flag_service.get_flag.side_effect = FlagValidationException(inner_exception=leaf)

        # when / then
        with pytest.raises(ReviewOrchestrationValidationException) as exc_info:
            service.explain_flag("does-not-exist")

        # The Foundation wrapper is carried through whole, so the leaf is one
        # level deeper than it used to be.
        assert isinstance(exc_info.value.inner_exception, FlagValidationException)
        assert exc_info.value.inner_exception.inner_exception is leaf

        mock_flag_service.get_flag.assert_called_once_with("does-not-exist")
        mock_retrieval_service.retrieve.assert_not_called()
        mock_generation_service.explain.assert_not_called()
