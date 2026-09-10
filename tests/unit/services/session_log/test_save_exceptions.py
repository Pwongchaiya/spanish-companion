"""Unit tests for SessionLogService's exception wrapping.

H3 of the architecture conformance audit: this service had none. These are
the checks that fail if a raw broker error escapes it again.
"""

import pytest

from api.models.foundations.session_log.exceptions import (
    SessionLogDependencyException,
    SessionLogServiceException,
    SessionLogUnavailableError,
)


class TestSaveExceptions:
    def test_wraps_broker_failure_as_dependency_exception(self, service, mock_session_log_broker, make_flag):
        mock_session_log_broker.write_session_log.side_effect = OSError("disk full")

        with pytest.raises(SessionLogDependencyException) as caught:
            service.save(["user: hola"], [make_flag()])

        assert isinstance(caught.value.inner_exception, SessionLogUnavailableError)
        assert mock_session_log_broker.write_session_log.call_count == 1

    def test_wraps_unexpected_failure_as_service_exception(self, service, mock_session_log_broker):
        # A non-string turn blows up in "\n".join before the broker is reached.
        with pytest.raises(SessionLogServiceException):
            service.save([object()], [])

        assert mock_session_log_broker.write_session_log.call_count == 0

    def test_empty_turns_short_circuits_without_touching_broker(self, service, mock_session_log_broker):
        assert service.save([], []) is None
        assert mock_session_log_broker.write_session_log.call_count == 0
