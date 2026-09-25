"""SessionAudioRecordingOrchestrationService: file+row coordination and prune sweep."""

from datetime import datetime
from unittest.mock import Mock, call

import pytest

from api.brokers.logging import LoggingBroker
from api.models.foundations.audio_storage.exceptions import AudioStorageDependencyException
from api.models.foundations.session_audio.exceptions import SessionAudioDependencyException
from api.models.foundations.session_audio.session_audio import SessionAudio
from api.models.orchestrations.session_audio_recording.exceptions import (
    SessionAudioRecordingOrchestrationDependencyException,
)
from api.services.foundations.audio_storage import IAudioStorageService
from api.services.foundations.session_audio import ISessionAudioService
from api.services.orchestrations.session_audio_recording import SessionAudioRecordingOrchestrationService

NOW = datetime(2026, 3, 31, 12, 0, 0)


@pytest.fixture
def storage():
    return Mock(spec=IAudioStorageService)


@pytest.fixture
def audio_service():
    return Mock(spec=ISessionAudioService)


@pytest.fixture
def logging_broker():
    return Mock(spec=LoggingBroker)


@pytest.fixture
def service(storage, audio_service, logging_broker):
    return SessionAudioRecordingOrchestrationService(storage, audio_service, lambda: NOW, logging_broker=logging_broker)


def test_save_recording_should_write_file_then_insert_row_with_computed_duration(service, storage, audio_service):
    storage.store_wav.return_value = "data/audio/session_4.wav"
    pcm = b"\x00\x00" * 48000  # 2s of 24kHz mono 16-bit
    audio_service.create_session_audio.side_effect = lambda row: row

    row = service.save_recording(4, pcm, 24000, 1)

    storage.store_wav.assert_called_once_with("session_4.wav", pcm, 24000, 1)
    audio_service.create_session_audio.assert_called_once_with(
        SessionAudio(None, 4, "data/audio/session_4.wav", 2.0, NOW)
    )
    assert row.duration_seconds == 2.0
    assert storage.remove_file.call_count == 0


def test_save_recording_should_remove_the_file_when_row_insert_fails(service, storage, audio_service, logging_broker):
    storage.store_wav.return_value = "data/audio/session_4.wav"
    audio_service.create_session_audio.side_effect = SessionAudioDependencyException(inner_exception=OSError("db"))

    with pytest.raises(SessionAudioRecordingOrchestrationDependencyException):
        service.save_recording(4, b"\x00\x00" * 100, 24000, 1)

    storage.remove_file.assert_called_once_with("data/audio/session_4.wav")
    assert logging_broker.log_error.call_count == 1


def test_save_recording_should_not_insert_when_file_write_fails(service, storage, audio_service):
    storage.store_wav.side_effect = AudioStorageDependencyException(inner_exception=OSError("disk full"))

    with pytest.raises(SessionAudioRecordingOrchestrationDependencyException):
        service.save_recording(4, b"\x00\x00", 24000, 1)

    assert audio_service.create_session_audio.call_count == 0
    assert storage.remove_file.call_count == 0


def test_prune_expired_should_delete_file_and_row_for_each_old_recording(service, storage, audio_service):
    old = [
        SessionAudio(1, 1, "a.wav", 5.0, datetime(2026, 1, 1)),
        SessionAudio(2, 2, "b.wav", 5.0, datetime(2026, 2, 1)),
    ]
    audio_service.list_session_audio_older_than.return_value = old

    assert service.prune_expired(30) == 2

    audio_service.list_session_audio_older_than.assert_called_once_with(datetime(2026, 3, 1, 12, 0, 0))
    assert storage.remove_file.call_args_list == [call("a.wav"), call("b.wav")]
    assert audio_service.delete_session_audio.call_args_list == [call(1), call(2)]


def test_prune_expired_should_continue_past_a_failing_row_and_keep_its_row_for_retry(
    service, storage, audio_service, logging_broker
):
    old = [
        SessionAudio(1, 1, "a.wav", 5.0, datetime(2026, 1, 1)),
        SessionAudio(2, 2, "b.wav", 5.0, datetime(2026, 1, 2)),
    ]
    audio_service.list_session_audio_older_than.return_value = old
    storage.remove_file.side_effect = [AudioStorageDependencyException(inner_exception=OSError("locked")), None]

    assert service.prune_expired(30) == 1

    assert audio_service.delete_session_audio.call_args_list == [call(2)]
    assert logging_broker.log_warning.call_count == 1
