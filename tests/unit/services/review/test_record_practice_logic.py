"""Unit tests for ReviewOrchestrator.record_practice() -- happy path.

See test_record_practice_exceptions.py for the unknown-flag_id refusal.

The attempt's timestamp comes from the injected fake clock, never
datetime.now() -- that is what makes the assertions below exact rather than
approximate.
"""

from api.brokers.practice_log import PracticeAttempt


class TestReviewOrchestratorRecordPractice:

    def test_should_record_attempt_stamped_with_the_injected_clock(
        self,
        service,
        mock_flag_broker,
        mock_practice_log_broker,
        clock,
        make_flag,
    ):
        # given
        flag = make_flag("flag-2")
        mock_flag_broker.load_flags.return_value = [make_flag("flag-1"), flag]

        # when
        actual = service.record_practice("flag-2", "fui al mercado ayer")

        # then
        expected = PracticeAttempt(
            flag_id="flag-2",
            attempt_text="fui al mercado ayer",
            timestamp=clock(),
        )
        assert actual == expected
        mock_flag_broker.load_flags.assert_called_once_with()
        mock_practice_log_broker.record_attempt.assert_called_once_with(expected)
        # The returned object is the very one handed to the broker, so the
        # caller has its timestamp without a second clock read.
        assert mock_practice_log_broker.record_attempt.call_args.args[0] is actual

    def test_should_stamp_the_current_clock_value_when_the_clock_has_advanced(
        self,
        service,
        mock_flag_broker,
        mock_practice_log_broker,
        clock,
        make_flag,
    ):
        # given
        mock_flag_broker.load_flags.return_value = [make_flag("flag-1")]
        clock.advance(90)

        # when
        actual = service.record_practice("flag-1", "fui al mercado")

        # then
        assert actual.timestamp == clock()
        mock_flag_broker.load_flags.assert_called_once_with()
        mock_practice_log_broker.record_attempt.assert_called_once_with(actual)
