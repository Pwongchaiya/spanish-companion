"""Unit tests for ReviewOrchestrator.record_practice() -- unknown flag_id.

An attempt against a flag that is not in the list is a client-side state
mismatch, not an orphan row worth writing -- so nothing must reach the
practice log.

The id is now rejected by FlagService, which raises FlagValidationException
wrapping NotFoundFlagException. Review re-wraps that whole exception rather
than unwrapping it, so the leaf sits at `.inner_exception.inner_exception`.
Whether the list was empty or merely lacked the id is no longer visible from
here -- that distinction belongs to FlagService's own tier. The blank
attempt_text refusal likewise moved down, to PracticeLogService's tier.
"""

import pytest

from api.models.flag.exceptions import FlagValidationException, NotFoundFlagException
from api.models.review.exceptions import ReviewOrchestrationValidationException


class TestReviewOrchestratorRecordPracticeExceptions:

    def test_should_raise_validation_exception_without_recording_when_flag_id_is_unknown(
        self,
        service,
        mock_flag_service,
        mock_practice_log_service,
    ):
        # given
        leaf = NotFoundFlagException("does-not-exist")
        mock_flag_service.get_flag.side_effect = FlagValidationException(inner_exception=leaf)

        # when / then
        with pytest.raises(ReviewOrchestrationValidationException) as exc_info:
            service.record_practice("does-not-exist", "fui al mercado")

        # The Foundation wrapper is carried through whole, so the leaf is one
        # level deeper than it used to be.
        assert isinstance(exc_info.value.inner_exception, FlagValidationException)
        assert exc_info.value.inner_exception.inner_exception is leaf

        mock_flag_service.get_flag.assert_called_once_with("does-not-exist")
        # The lookup runs first, so a bad id short-circuits before any write
        # is attempted -- and before PracticeLogService gets a chance to
        # reject the text.
        mock_practice_log_service.record_attempt.assert_not_called()
