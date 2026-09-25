"""Happy path: each public method delegates to exactly one broker call and
returns its result unchanged. Strict call-count verification."""

import pytest

from api.models.foundations.session_audio.exceptions import (
    NotFoundSessionAudioException,
    SessionAudioValidationException,
)
from datetime import datetime

FIXED_TIME = datetime(2026, 1, 2, 10, 0, 0)

_BROKER_METHODS = (
    "insert_session_audio",
    "select_session_audio_by_session_log_id",
    "select_session_audio_older_than",
    "delete_session_audio",
)


def _assert_only(broker, called: str):
    for name in _BROKER_METHODS:
        assert getattr(broker, name).call_count == (1 if name == called else 0), name


def test_create_should_insert_and_return_broker_row(service, mock_session_audio_broker, make_session_audio):
    submitted, stored = make_session_audio(), make_session_audio(id=7)
    mock_session_audio_broker.insert_session_audio.return_value = stored

    assert service.create_session_audio(submitted) is stored
    mock_session_audio_broker.insert_session_audio.assert_called_once_with(submitted)
    _assert_only(mock_session_audio_broker, "insert_session_audio")


def test_get_by_session_log_id_should_return_row(service, mock_session_audio_broker, make_session_audio):
    row = make_session_audio(id=3)
    mock_session_audio_broker.select_session_audio_by_session_log_id.return_value = row

    assert service.get_session_audio_by_session_log_id(4) is row
    mock_session_audio_broker.select_session_audio_by_session_log_id.assert_called_once_with(4)
    _assert_only(mock_session_audio_broker, "select_session_audio_by_session_log_id")


def test_get_by_session_log_id_should_raise_not_found_when_broker_returns_none(service, mock_session_audio_broker):
    mock_session_audio_broker.select_session_audio_by_session_log_id.return_value = None

    with pytest.raises(SessionAudioValidationException) as caught:
        service.get_session_audio_by_session_log_id(4)

    assert isinstance(caught.value.inner_exception, NotFoundSessionAudioException)
    _assert_only(mock_session_audio_broker, "select_session_audio_by_session_log_id")


def test_list_older_than_should_return_broker_rows(service, mock_session_audio_broker, make_session_audio):
    rows = [make_session_audio(id=1), make_session_audio(id=2)]
    mock_session_audio_broker.select_session_audio_older_than.return_value = rows

    assert service.list_session_audio_older_than(FIXED_TIME) == rows
    mock_session_audio_broker.select_session_audio_older_than.assert_called_once_with(FIXED_TIME)
    _assert_only(mock_session_audio_broker, "select_session_audio_older_than")


def test_delete_should_return_deleted_row(service, mock_session_audio_broker, make_session_audio):
    row = make_session_audio(id=9)
    mock_session_audio_broker.delete_session_audio.return_value = row

    assert service.delete_session_audio(9) is row
    mock_session_audio_broker.delete_session_audio.assert_called_once_with(9)
    _assert_only(mock_session_audio_broker, "delete_session_audio")


def test_delete_should_raise_not_found_when_missing(service, mock_session_audio_broker):
    mock_session_audio_broker.delete_session_audio.return_value = None

    with pytest.raises(SessionAudioValidationException) as caught:
        service.delete_session_audio(9)

    assert isinstance(caught.value.inner_exception, NotFoundSessionAudioException)


def test_get_latest_should_return_broker_row(service, mock_session_audio_broker, make_session_audio):
    row = make_session_audio(id=8)
    mock_session_audio_broker.select_latest_session_audio.return_value = row

    assert service.get_latest_session_audio() is row
    assert mock_session_audio_broker.select_latest_session_audio.call_count == 1
    _assert_only(mock_session_audio_broker, "select_latest_session_audio")


def test_get_latest_should_raise_not_found_when_nothing_recorded(service, mock_session_audio_broker):
    mock_session_audio_broker.select_latest_session_audio.return_value = None

    with pytest.raises(SessionAudioValidationException) as caught:
        service.get_latest_session_audio()

    assert isinstance(caught.value.inner_exception, NotFoundSessionAudioException)
