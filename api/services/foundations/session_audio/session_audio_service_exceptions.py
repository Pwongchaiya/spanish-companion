"""Catch/wrap/log helpers for SessionAudioService.

Same dispatch shape as PersonaServiceExceptions minus the unique-violation
tier (session_audio has no unique constraint): Validation (invalid input + not
found), Dependency (any SQLAlchemyError), catch-all Service.
"""

from typing import Callable, TypeVar

from sqlalchemy.exc import SQLAlchemyError

from api.models.foundations.session_audio.exceptions import (
    FailedSessionAudioStorageException,
    InvalidSessionAudioException,
    NotFoundSessionAudioException,
    SessionAudioDependencyException,
    SessionAudioServiceException,
    SessionAudioValidationException,
)

T = TypeVar("T")


class SessionAudioServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        try:
            return fn()
        except (InvalidSessionAudioException, NotFoundSessionAudioException) as e:
            raise self._create_and_log_validation_exception(e) from e
        except SQLAlchemyError as e:
            raise self._create_and_log_dependency_exception(FailedSessionAudioStorageException(str(e))) from e
        except Exception as e:
            raise self._create_and_log_service_exception(e) from e

    def _create_and_log_validation_exception(self, exception: Exception) -> SessionAudioValidationException:
        validation_exception = SessionAudioValidationException(inner_exception=exception)
        self._logging_broker.log_error(validation_exception)
        return validation_exception

    def _create_and_log_dependency_exception(self, exception: Exception) -> SessionAudioDependencyException:
        dependency_exception = SessionAudioDependencyException(inner_exception=exception)
        self._logging_broker.log_error(dependency_exception)
        return dependency_exception

    def _create_and_log_service_exception(self, exception: Exception) -> SessionAudioServiceException:
        service_exception = SessionAudioServiceException(inner_exception=exception)
        self._logging_broker.log_error(service_exception)
        return service_exception
