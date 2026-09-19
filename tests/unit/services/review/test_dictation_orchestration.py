"""Unit tests for ReviewOrchestrationService dictation-back (Phase 5 E2).

Deterministic data only: flag timestamps are fixed, nothing reads a live clock.
"""

from datetime import datetime

import pytest

from api.models.foundations.flag import Flag
from api.models.foundations.flag.exceptions import FlagValidationException, NotFoundFlagException
from api.models.orchestrations.review.dictation import DictationExercise
from api.models.orchestrations.review.exceptions import (
    ReviewOrchestrationServiceException,
    ReviewOrchestrationValidationException,
)


def flag(flag_id, corrected="yo tengo", count=1, day=1, channel="grammar"):
    return Flag(
        id=flag_id,
        said="yo soy tener",
        corrected=corrected,
        category="verb_conjugation",
        timestamp=datetime(2026, 9, day),
        channel=channel,
        occurrence_count=count,
    )


class TestGetDictationExercise:

    def test_should_pick_highest_occurrence_count(self, service, mock_flag_service):
        mock_flag_service.list_flags.return_value = [flag("a", count=1, day=9), flag("b", "él está", count=3, day=1)]

        actual = service.get_dictation_exercise()

        assert actual == DictationExercise(flag_id="b", target="él está")
        mock_flag_service.list_flags.assert_called_once_with()

    def test_should_break_count_ties_with_newest_timestamp(self, service, mock_flag_service):
        mock_flag_service.list_flags.return_value = [flag("a", day=1), flag("b", day=5)]

        assert service.get_dictation_exercise().flag_id == "b"

    def test_should_skip_excluded_and_blank_corrected_flags(self, service, mock_flag_service):
        mock_flag_service.list_flags.return_value = [flag("a", count=9), flag("b", "  "), flag("c", count=1)]

        assert service.get_dictation_exercise(exclude_flag_id="a").flag_id == "c"

    def test_should_return_none_when_nothing_eligible(self, service, mock_flag_service):
        mock_flag_service.list_flags.return_value = [flag("a")]

        assert service.get_dictation_exercise(exclude_flag_id="a") is None
        mock_flag_service.list_flags.assert_called_once_with()

    def test_should_wrap_broker_failure_as_service_exception(self, service, mock_flag_service):
        mock_flag_service.list_flags.side_effect = OSError("disk")

        with pytest.raises(ReviewOrchestrationServiceException):
            service.get_dictation_exercise()
        mock_flag_service.list_flags.assert_called_once_with()


class TestCheckDictation:

    def test_should_report_match_and_not_persist(self, service, mock_flag_service, mock_practice_log_service):
        mock_flag_service.get_flag.return_value = flag("a", "Yo tengo")

        actual = service.check_dictation("a", "yo tengo.")

        assert actual.matches is True
        assert actual.target == "Yo tengo"
        assert actual.typed_text == "yo tengo."
        mock_flag_service.get_flag.assert_called_once_with("a")
        mock_practice_log_service.record_attempt.assert_not_called()

    def test_should_report_accent_difference_as_mismatch(self, service, mock_flag_service):
        mock_flag_service.get_flag.return_value = flag("a", "él está")

        actual = service.check_dictation("a", "el esta")

        assert actual.matches is False
        assert [w.status for w in actual.words] == ["accent", "accent"]
        mock_flag_service.get_flag.assert_called_once_with("a")

    def test_should_wrap_unknown_flag_as_validation_exception(self, service, mock_flag_service):
        leaf = NotFoundFlagException("nope")
        mock_flag_service.get_flag.side_effect = FlagValidationException(inner_exception=leaf)

        with pytest.raises(ReviewOrchestrationValidationException) as exc_info:
            service.check_dictation("nope", "yo tengo")

        assert exc_info.value.inner_exception.inner_exception is leaf
        mock_flag_service.get_flag.assert_called_once_with("nope")

    def test_should_wrap_blank_typed_as_service_exception(self, service, mock_flag_service):
        mock_flag_service.get_flag.return_value = flag("a")

        with pytest.raises(ReviewOrchestrationServiceException):
            service.check_dictation("a", "  ")
        mock_flag_service.get_flag.assert_called_once_with("a")
