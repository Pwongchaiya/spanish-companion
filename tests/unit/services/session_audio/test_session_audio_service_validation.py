"""Bad input is rejected before any broker call, with every failing field
reported in one InvalidSessionAudioException."""

import pytest

from api.models.foundations.session_audio.exceptions import (
    InvalidSessionAudioException,
    SessionAudioValidationException,
)


def _no_broker_calls(broker):
    for name in (
        "insert_session_audio",
        "select_session_audio_by_session_log_id",
        "select_session_audio_older_than",
        "delete_session_audio",
    ):
        assert getattr(broker, name).call_count == 0, name


def test_create_should_report_every_failing_field(service, mock_session_audio_broker, make_session_audio):
    bad = make_session_audio(session_log_id=0, file_path=" ", duration_seconds=-1.0, created_at=None)

    with pytest.raises(SessionAudioValidationException) as caught:
        service.create_session_audio(bad)

    leaf = caught.value.inner_exception
    assert isinstance(leaf, InvalidSessionAudioException)
    assert set(leaf.errors) == {"session_log_id", "file_path", "duration_seconds", "created_at"}
    _no_broker_calls(mock_session_audio_broker)


def test_create_should_reject_none(service, mock_session_audio_broker):
    with pytest.raises(SessionAudioValidationException) as caught:
        service.create_session_audio(None)

    assert set(caught.value.inner_exception.errors) == {"session_audio"}
    _no_broker_calls(mock_session_audio_broker)


@pytest.mark.parametrize("bad_id", [0, -1, True, "4", None])
def test_lookup_and_delete_should_reject_invalid_id(service, mock_session_audio_broker, bad_id):
    for call in (service.get_session_audio_by_session_log_id, service.delete_session_audio):
        with pytest.raises(SessionAudioValidationException):
            call(bad_id)
    _no_broker_calls(mock_session_audio_broker)


def test_list_older_than_should_reject_non_datetime(service, mock_session_audio_broker):
    with pytest.raises(SessionAudioValidationException):
        service.list_session_audio_older_than("2026-01-01")
    _no_broker_calls(mock_session_audio_broker)
