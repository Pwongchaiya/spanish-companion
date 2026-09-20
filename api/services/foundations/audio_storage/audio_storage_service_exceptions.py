"""Catch/wrap/log helpers for AudioStorageService: Validation, Dependency (OSError), Service."""

from typing import Callable, TypeVar

from api.models.foundations.audio_storage.exceptions import (
    AudioStorageDependencyException,
    AudioStorageServiceException,
    AudioStorageValidationException,
    FailedAudioStorageException,
    InvalidAudioStorageException,
)

T = TypeVar("T")


class AudioStorageServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        try:
            return fn()
        except InvalidAudioStorageException as e:
            raise self._log(AudioStorageValidationException(inner_exception=e)) from e
        except OSError as e:
            raise self._log(AudioStorageDependencyException(inner_exception=FailedAudioStorageException(str(e)))) from e
        except Exception as e:
            raise self._log(AudioStorageServiceException(inner_exception=e)) from e

    def _log(self, exception: Exception) -> Exception:
        self._logging_broker.log_error(exception)
        return exception
