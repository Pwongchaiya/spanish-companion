"""Unit tests for LiveTranscriptService.read_full_text() -- roadmap A6's
read-back of a just-ended session's transcript, for the CEFR estimate."""

import pytest

from api.models.foundations.live_transcript.exceptions import (
    LiveTranscriptDependencyException,
    LiveTranscriptUnavailableError,
)


class TestLiveTranscriptServiceReadFullText:

    def test_should_format_jsonl_lines_as_role_text(self, service, mock_session_log_broker):
        # given
        mock_session_log_broker.read_transcript.return_value = (
            '{"role": "user", "text": "hola"}\n{"role": "assistant", "text": "\\u00a1hola!"}\n'
        )

        # when
        text = service.read_full_text()

        # then
        assert text == "[user] hola\n[assistant] \u00a1hola!"

    def test_should_return_empty_string_when_no_transcript_written(self, service, mock_session_log_broker):
        # given
        mock_session_log_broker.read_transcript.return_value = ""

        # when
        text = service.read_full_text()

        # then
        assert text == ""

    def test_should_skip_malformed_lines_without_raising(self, service, mock_session_log_broker):
        # given
        mock_session_log_broker.read_transcript.return_value = 'not json\n{"role": "user", "text": "hola"}\n'

        # when
        text = service.read_full_text()

        # then
        assert text == "[user] hola"

    def test_wraps_broker_failure_as_dependency_exception(self, service, mock_session_log_broker):
        mock_session_log_broker.read_transcript.side_effect = OSError("disk error")

        with pytest.raises(LiveTranscriptDependencyException) as caught:
            service.read_full_text()

        assert isinstance(caught.value.inner_exception, LiveTranscriptUnavailableError)
