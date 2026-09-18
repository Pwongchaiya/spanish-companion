"""Unit tests for ReviewOrchestrationService.record_practice() -- happy path.

See test_record_practice_exceptions.py for the unknown-flag_id refusal.

The attempt's timestamp comes from the injected fake clock, never
datetime.now() -- that is what makes the assertions below exact rather than
approximate.

LearnerProfile Phase 2: record_practice() now also judges the attempt and
writes the verdict to mistake_pattern via the two new Processing
dependencies -- see test_record_practice_mistake_pattern.py for that half.
"""

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
        mock_generation_service.judge_practice_attempt.return_value = True

        # when
        actual = service.record_practice("flag-2", "fui al mercado ayer")

        # then
        expected_attempt = PracticeAttempt(
            flag_id="flag-2",
            attempt_text="fui al mercado ayer",
            timestamp=clock(),
        )
        assert actual == PracticeResult(attempt=expected_attempt, mastered=True)
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
        mock_generation_service.judge_practice_attempt.return_value = False
        clock.advance(90)

        # when
        actual = service.record_practice("flag-1", "fui al mercado")

        # then
        assert actual.attempt.timestamp == clock()
        mock_flag_service.get_flag.assert_called_once_with("flag-1")
        mock_practice_log_service.record_attempt.assert_called_once_with(actual.attempt)
