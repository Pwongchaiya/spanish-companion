"""Unit tests for ReviewOrchestrationService.record_practice() -- happy path.

See test_record_practice_exceptions.py for the unknown-flag_id refusal.

The attempt's timestamp comes from the injected fake clock, never
datetime.now() -- that is what makes the assertions below exact rather than
approximate.

LearnerProfile Phase 2: record_practice() now also judges the attempt and
writes the verdict to mistake_pattern via the two new Processing
dependencies -- see test_record_practice_mistake_pattern.py for that half.

A2 (graded practice-attempt verdict): `mastered` is now derived from the
judge's grade word (`grade in ("good", "easy")`) instead of being the judge's
direct return value -- see TestReviewOrchestratorMasteredDerivation below.
"""

import pytest

from api.brokers.practice_log import PracticeAttempt
from api.models.orchestrations.review.practice_result import PracticeResult


class TestReviewOrchestratorRecordPractice:

    def test_should_record_attempt_stamped_with_the_injected_clock(
        self,
        service,
        mock_flag_service,
        mock_practice_log_service,
        mock_generation_service,
        clock,
        make_flag,
    ):
        # given
        mock_flag_service.get_flag.return_value = make_flag("flag-2")
        mock_generation_service.judge_practice_attempt.return_value = "good"

        # when
        actual = service.record_practice("flag-2", "fui al mercado ayer")

        # then
        expected_attempt = PracticeAttempt(
            flag_id="flag-2",
            attempt_text="fui al mercado ayer",
            timestamp=clock(),
            grade="good",
        )
        assert actual == PracticeResult(attempt=expected_attempt, mastered=True, grade="good")
        mock_flag_service.get_flag.assert_called_once_with("flag-2")
        mock_practice_log_service.record_attempt.assert_called_once_with(expected_attempt)
        # The logged attempt is the very one returned, so the caller has its
        # timestamp without a second clock read.
        assert mock_practice_log_service.record_attempt.call_args.args[0] is actual.attempt

    def test_should_stamp_the_current_clock_value_when_the_clock_has_advanced(
        self,
        service,
        mock_flag_service,
        mock_practice_log_service,
        mock_generation_service,
        clock,
        make_flag,
    ):
        # given
        mock_flag_service.get_flag.return_value = make_flag("flag-1")
        mock_generation_service.judge_practice_attempt.return_value = "again"
        clock.advance(90)

        # when
        actual = service.record_practice("flag-1", "fui al mercado")

        # then
        assert actual.attempt.timestamp == clock()
        mock_flag_service.get_flag.assert_called_once_with("flag-1")
        mock_practice_log_service.record_attempt.assert_called_once_with(actual.attempt)


class TestReviewOrchestratorMasteredDerivation:
    """A2: `mastered` is derived from the judge's grade word, not returned
    by it directly -- "good"/"easy" master the flag, "again"/"hard" don't.
    """

    @pytest.mark.parametrize(
        "grade,expected_mastered",
        [("again", False), ("hard", False), ("good", True), ("easy", True)],
    )
    def test_should_derive_mastered_from_grade(
        self,
        service,
        mock_flag_service,
        mock_practice_log_service,
        mock_generation_service,
        make_flag,
        grade,
        expected_mastered,
    ):
        # given
        mock_flag_service.get_flag.return_value = make_flag("flag-1")
        mock_generation_service.judge_practice_attempt.return_value = grade

        # when
        actual = service.record_practice("flag-1", "fui al mercado")

        # then
        assert actual.grade == grade
        assert actual.mastered is expected_mastered
        assert actual.attempt.grade == grade
        # The persisted record carries the grade too -- the JSONL log is
        # append-only, so grade has to be known before the write, not patched in after.
        mock_practice_log_service.record_attempt.assert_called_once_with(actual.attempt)
