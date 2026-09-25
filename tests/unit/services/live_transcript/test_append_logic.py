"""Unit tests for LiveTranscriptService.append()/clear() -- JSON-line
formatting moved verbatim from the old _write_live_transcript() loop."""


class TestLiveTranscriptServiceAppend:

    def test_should_write_json_line_with_role_and_text(self, service, mock_session_log_broker):
        # when
        service.append("user", "hola")

        # then
        mock_session_log_broker.append_transcript_line.assert_called_once_with('{"role": "user", "text": "hola"}')

    def test_should_preserve_non_ascii_text_unescaped(self, service, mock_session_log_broker):
        # when -- ensure_ascii=False must be preserved, or accented Spanish
        # in the live transcript comes out as \uXXXX escapes instead of the
        # literal character.
        service.append("assistant", "cómo estás")

        # then
        mock_session_log_broker.append_transcript_line.assert_called_once_with(
            '{"role": "assistant", "text": "cómo estás"}'
        )


class TestLiveTranscriptServiceClear:

    def test_should_delegate_to_broker(self, service, mock_session_log_broker):
        # when
        service.clear()

        # then
        mock_session_log_broker.clear_transcript.assert_called_once_with()
