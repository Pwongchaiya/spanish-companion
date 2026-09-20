"""Exception dispatch: which raw failure maps to which wrapper tier, and that
every wrap is logged exactly once."""

import pytest
from sqlalchemy.exc import OperationalError

from api.models.foundations.session_audio.exceptions import (
    FailedSessionAudioStorageException,
    SessionAudioDependencyException,
    SessionAudioServiceException,
)
from datetime import datetime

FIXED_TIME = datetime(2026, 1, 2, 10, 0, 0)


@pytest.mark.parametrize(
    "call, broker_method, args",
    [
        ("get_session_audio_by_session_log_id", "select_session_audio_by_session_log_id", (4,)),
        ("list_session_audio_older_than", "select_session_audio_older_than", (FIXED_TIME,)),
        ("delete_session_audio", "delete_session_audio", (1,)),
    ],
)
def test_should_wrap_sqlalchemy_error_as_dependency_exception(
    service, mock_session_audio_broker, mock_logging_broker, call, broker_method, args
):
    getattr(mock_session_audio_broker, broker_method).side_effect = OperationalError(
        "SQL", {}, Exception("connection refused")
    )

    with pytest.raises(SessionAudioDependencyException) as caught:
        getattr(service, call)(*args)

    assert isinstance(caught.value.inner_exception, FailedSessionAudioStorageException)
    assert getattr(mock_session_audio_broker, broker_method).call_count == 1
    assert mock_logging_broker.log_error.call_count == 1


def test_create_should_wrap_sqlalchemy_error_as_dependency_exception(
    service, mock_session_audio_broker, mock_logging_broker, make_session_audio
):
    mock_session_audio_broker.insert_session_audio.side_effect = OperationalError(
        "INSERT", {}, Exception("connection refused")
    )

    with pytest.raises(SessionAudioDependencyException):
        service.create_session_audio(make_session_audio())

    assert mock_session_audio_broker.insert_session_audio.call_count == 1
    assert mock_logging_broker.log_error.call_count == 1


def test_should_wrap_unexpected_error_as_service_exception(
    service, mock_session_audio_broker, mock_logging_broker
):
    boom = RuntimeError("boom")
    mock_session_audio_broker.delete_session_audio.side_effect = boom

    with pytest.raises(SessionAudioServiceException) as caught:
        service.delete_session_audio(1)

    assert caught.value.inner_exception is boom
    assert mock_logging_broker.log_error.call_count == 1
