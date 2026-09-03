"""Unit tests for PracticeLogService.record_attempt() -- happy path.

See test_record_attempt_validation.py for the blank-text refusal and
test_record_attempt_exceptions.py for the broker-failure path.
"""


class TestPracticeLogServiceRecordAttempt:

    def test_should_record_attempt_when_attempt_text_is_valid(
        self, service, mock_practice_log_broker, make_attempt
    ):
        # given
        attempt = make_attempt()

        # when
        service.record_attempt(attempt)

        # then
        mock_practice_log_broker.record_attempt.assert_called_once_with(attempt)
