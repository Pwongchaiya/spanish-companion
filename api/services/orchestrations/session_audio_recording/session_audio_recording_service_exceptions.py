"""Catch/wrap/log helpers for SessionAudioRecordingOrchestrationService (three tiers)."""

from typing import Callable, TypeVar

from api.models.foundations.audio_storage.exceptions import (
    AudioStorageDependencyException,
    AudioStorageValidationException,
)
from api.models.foundations.session_audio.exceptions import (
    SessionAudioDependencyException,
    SessionAudioValidationException,
)
from api.models.orchestrations.session_audio_recording.exceptions import (
    FailedSessionAudioRecordingOrchestrationServiceException,
    SessionAudioRecordingOrchestrationDependencyException,
    SessionAudioRecordingOrchestrationServiceException,
    SessionAudioRecordingOrchestrationValidationException,
)

T = TypeVar("T")


class SessionAudioRecordingOrchestrationServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        try:
            return fn()
        except (AudioStorageValidationException, SessionAudioValidationException) as e:
            raise self._log(SessionAudioRecordingOrchestrationValidationException(inner_exception=e)) from e
        except (AudioStorageDependencyException, SessionAudioDependencyException) as e:
            raise self._log(SessionAudioRecordingOrchestrationDependencyException(inner_exception=e)) from e
        except Exception as e:
            failed = FailedSessionAudioRecordingOrchestrationServiceException(inner_exception=e)
            raise self._log(SessionAudioRecordingOrchestrationServiceException(inner_exception=failed)) from e

    def _log(self, exception: Exception) -> Exception:
        self._logging_broker.log_error(exception)
        return exception
