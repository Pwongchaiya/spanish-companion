"""Unit tests for PracticeLogService.read_attempts() -- happy path.

See test_read_attempts_exceptions.py for the broker-failure path.
"""


class TestPracticeLogServiceReadAttempts:

    def test_should_return_all_attempts_when_flag_id_is_not_given(
        self, service, mock_practice_log_broker, make_attempt
    ):
        # given
        attempts = [make_attempt("flag-1"), make_attempt("flag-2")]
        mock_practice_log_broker.read_attempts.return_value = attempts

        # when
        actual = service.read_attempts()

        # then
        assert actual == attempts
        mock_practice_log_broker.read_attempts.assert_called_once_with(None)

    def test_should_return_only_matching_attempts_when_flag_id_is_given(
        self, service, mock_practice_log_broker, make_attempt
    ):
        # given
        attempts = [make_attempt("flag-1")]
        mock_practice_log_broker.read_attempts.return_value = attempts

        # when
        actual = service.read_attempts("flag-1")

        # then
        assert actual == attempts
        mock_practice_log_broker.read_attempts.assert_called_once_with("flag-1")

    def test_should_return_empty_list_when_no_attempts_match(self, service, mock_practice_log_broker):
        # given
        mock_practice_log_broker.read_attempts.return_value = []

        # when
        actual = service.read_attempts("flag-unused")

        # then
        assert actual == []
        mock_practice_log_broker.read_attempts.assert_called_once_with("flag-unused")
