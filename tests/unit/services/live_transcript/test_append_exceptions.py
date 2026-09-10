"""Unit tests for LiveTranscriptService's exception wrapping.

H3 of the architecture conformance audit: this service had none. These are
the checks that fail if a raw broker error escapes it again.
"""

import pytest

from api.models.foundations.live_transcript.exceptions import (
    LiveTranscriptDependencyException,
    LiveTranscriptServiceException,
    LiveTranscriptUnavailableError,
)


class TestAppendExceptions:
    def test_wraps_broker_failure_as_dependency_exception(self, service, mock_session_log_broker):
        broker_error = OSError("disk full")
        mock_session_log_broker.append_transcript_line.side_effect = broker_error

        with pytest.raises(LiveTranscriptDependencyException) as caught:
            service.append("user", "hola")

        assert isinstance(caught.value.inner_exception, LiveTranscriptUnavailableError)
        assert mock_session_log_broker.append_transcript_line.call_count == 1

    def test_wraps_unexpected_failure_as_service_exception(self, service, mock_session_log_broker):
        # json.dumps fails before the broker is ever reached -- the catch-all path.
        with pytest.raises(LiveTranscriptServiceException):
            service.append("user", object())

        assert mock_session_log_broker.append_transcript_line.call_count == 0


class TestClearExceptions:
    def test_wraps_broker_failure_as_dependency_exception(self, service, mock_session_log_broker):
        mock_session_log_broker.clear_transcript.side_effect = OSError("permission denied")

        with pytest.raises(LiveTranscriptDependencyException) as caught:
            service.clear()

        assert isinstance(caught.value.inner_exception, LiveTranscriptUnavailableError)
        assert mock_session_log_broker.clear_transcript.call_count == 1
