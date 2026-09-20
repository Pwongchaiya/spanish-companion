"""Foundation service for local-disk audio storage. One broker, validation only."""

from api.brokers.audio_storage.i_audio_storage_broker import IAudioStorageBroker
from api.brokers.logging import LoggingBroker
from api.services.foundations.audio_storage.audio_storage_service_exceptions import AudioStorageServiceExceptions
from api.services.foundations.audio_storage.audio_storage_service_validations import AudioStorageServiceValidations
from api.services.foundations.audio_storage.i_audio_storage_service import IAudioStorageService


class AudioStorageService(AudioStorageServiceExceptions, AudioStorageServiceValidations, IAudioStorageService):
    """Owns validated WAV writes and deletes."""

    def __init__(self, audio_storage_broker: IAudioStorageBroker, *, logging_broker: LoggingBroker) -> None:
        self._audio_storage_broker = audio_storage_broker
        self._logging_broker = logging_broker

    def store_wav(self, file_name: str, pcm: bytes, sample_rate: int, num_channels: int) -> str:
        def action() -> str:
            self._validate_wav(file_name, pcm, sample_rate, num_channels)
            return self._audio_storage_broker.write_wav(file_name, pcm, sample_rate, num_channels)

        return self._try_catch(action)

    def remove_file(self, file_path: str) -> None:
        def action() -> None:
            self._validate_file_path(file_path)
            self._audio_storage_broker.delete_file(file_path)

        return self._try_catch(action)
