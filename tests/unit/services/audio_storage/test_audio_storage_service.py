"""AudioStorageService: delegation, validation-before-broker, OSError -> dependency tier."""

from unittest.mock import Mock

import pytest

from api.brokers.audio_storage import IAudioStorageBroker
from api.models.foundations.audio_storage.exceptions import (
    AudioStorageDependencyException,
    AudioStorageServiceException,
    AudioStorageValidationException,
)
from api.services.foundations.audio_storage import AudioStorageService
from tests.unit.services._api_logging_fixture import mock_logging_broker  # noqa: F401


@pytest.fixture
def broker():
    return Mock(spec=IAudioStorageBroker)


@pytest.fixture
def service(broker, mock_logging_broker):
    return AudioStorageService(broker, logging_broker=mock_logging_broker)


def test_store_wav_should_delegate_and_return_path(service, broker):
    broker.write_wav.return_value = "data/audio/s1.wav"

    assert service.store_wav("s1.wav", b"\x00\x01", 24000, 1) == "data/audio/s1.wav"
    broker.write_wav.assert_called_once_with("s1.wav", b"\x00\x01", 24000, 1)
    assert broker.delete_file.call_count == 0


def test_remove_file_should_delegate(service, broker):
    service.remove_file("data/audio/s1.wav")

    broker.delete_file.assert_called_once_with("data/audio/s1.wav")
    assert broker.write_wav.call_count == 0


@pytest.mark.parametrize(
    "args", [(" ", b"x", 24000, 1), ("a.wav", b"", 24000, 1), ("a.wav", b"x", 0, 1), ("a.wav", b"x", 24000, True)]
)
def test_store_wav_should_reject_bad_input_before_broker(service, broker, args):
    with pytest.raises(AudioStorageValidationException):
        service.store_wav(*args)
    assert broker.write_wav.call_count == 0


def test_remove_file_should_reject_blank_path(service, broker):
    with pytest.raises(AudioStorageValidationException):
        service.remove_file("")
    assert broker.delete_file.call_count == 0


def test_should_wrap_oserror_as_dependency_and_log_once(service, broker, mock_logging_broker):
    broker.write_wav.side_effect = OSError("disk full")

    with pytest.raises(AudioStorageDependencyException):
        service.store_wav("a.wav", b"x", 24000, 1)

    assert broker.write_wav.call_count == 1
    assert mock_logging_broker.log_error.call_count == 1


def test_should_wrap_unexpected_error_as_service_exception(service, broker):
    broker.delete_file.side_effect = RuntimeError("boom")

    with pytest.raises(AudioStorageServiceException):
        service.remove_file("a.wav")
