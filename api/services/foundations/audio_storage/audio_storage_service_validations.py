"""Validation checks for AudioStorageService (batched, same pattern as SessionAudioServiceValidations)."""

from api.models.foundations.audio_storage.exceptions import InvalidAudioStorageException


def _is_blank(value: object) -> bool:
    return not isinstance(value, str) or not value.strip()


def _is_positive_int(value: object) -> bool:
    return not isinstance(value, int) or isinstance(value, bool) or value <= 0


class AudioStorageServiceValidations:
    """Mixin: raises InvalidAudioStorageException with every failing field attached."""

    def _validate_wav(self, file_name: object, pcm: object, sample_rate: object, num_channels: object) -> None:
        self._validate(
            (_is_blank(file_name), "file_name", "File name is required"),
            (not isinstance(pcm, (bytes, bytearray)) or len(pcm) == 0, "pcm", "Audio data is required"),
            (_is_positive_int(sample_rate), "sample_rate", "Sample rate must be a positive integer"),
            (_is_positive_int(num_channels), "num_channels", "Channel count must be a positive integer"),
        )

    def _validate_file_path(self, file_path: object) -> None:
        self._validate((_is_blank(file_path), "file_path", "File path is required"))

    @staticmethod
    def _validate(*rules: tuple[bool, str, str]) -> None:
        exception = InvalidAudioStorageException()
        for condition, field, message in rules:
            if condition:
                exception.upsert_data_list(field, message)
        exception.throw_if_contains_errors()
