"""Catch/wrap/log helpers for SessionReplayOrchestrationService.

Same three-tier shape as PronunciationOrchestrationServiceExceptions. The
validation tier carries either a Foundation validation wrapper (missing audio)
or the NotFoundSessionReplayException leaf (missing session) through whole.
"""

from typing import Callable, TypeVar

from api.models.foundations.flag.exceptions import FlagDependencyException
from api.models.foundations.session_audio.exceptions import (
    SessionAudioDependencyException,
    SessionAudioValidationException,
)
from api.models.foundations.session_log_entry.exceptions import SessionLogEntryDependencyException
from api.models.orchestrations.session_replay.exceptions import (
    FailedSessionReplayOrchestrationServiceException,
    NotFoundSessionReplayException,
    SessionReplayOrchestrationDependencyException,
    SessionReplayOrchestrationServiceException,
    SessionReplayOrchestrationValidationException,
)

T = TypeVar("T")


class SessionReplayOrchestrationServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        try:
            return fn()
        except (SessionAudioValidationException, NotFoundSessionReplayException) as e:
            raise self._log(SessionReplayOrchestrationValidationException(inner_exception=e)) from e
        except (SessionAudioDependencyException, FlagDependencyException, SessionLogEntryDependencyException) as e:
            raise self._log(SessionReplayOrchestrationDependencyException(inner_exception=e)) from e
        except Exception as e:
            failed = FailedSessionReplayOrchestrationServiceException(inner_exception=e)
            raise self._log(SessionReplayOrchestrationServiceException(inner_exception=failed)) from e

    def _log(self, exception: Exception) -> Exception:
        self._logging_broker.log_error(exception)
        return exception
