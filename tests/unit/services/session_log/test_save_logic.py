"""Unit tests for SessionLogService.save() -- formatting + the empty-turns
short-circuit, moved verbatim from the old save_session_log() free function."""

from pathlib import Path


class TestSessionLogServiceSave:

    def test_should_return_none_without_calling_broker_when_turns_is_empty(
        self, service, mock_session_log_broker, make_flag
    ):
        # when
        result = service.save([], [make_flag()])

        # then
        assert result is None
        mock_session_log_broker.write_session_log.assert_not_called()

    def test_should_write_turns_only_when_no_flags(self, service, mock_session_log_broker):
        # given
        mock_session_log_broker.write_session_log.return_value = Path("/tmp/log.log")
        turns = ["[user] hola", "[assistant] hola, como estas"]

        # when
        result = service.save(turns, [])

        # then
        assert result == Path("/tmp/log.log")
        mock_session_log_broker.write_session_log.assert_called_once_with("[user] hola\n[assistant] hola, como estas\n")

    def test_should_append_flags_section_when_flags_exist(self, service, mock_session_log_broker, make_flag):
        # given
        mock_session_log_broker.write_session_log.return_value = Path("/tmp/log.log")
        turns = ["[user] hola"]
        flag = make_flag(category="verb_conjugation")

        # when
        service.save(turns, [flag])

        # then
        mock_session_log_broker.write_session_log.assert_called_once_with(
            "[user] hola\n--- flags ---\n"
            '[verb_conjugation] said: "iba al mercado ayer" -> corrected: "fui al mercado ayer"\n'
        )

    def test_should_return_brokers_path_when_write_succeeds(self, service, mock_session_log_broker):
        # given
        mock_session_log_broker.write_session_log.return_value = Path("/tmp/2026-01-02-030405.log")

        # when
        result = service.save(["[user] hola"], [])

        # then
        assert result == Path("/tmp/2026-01-02-030405.log")
