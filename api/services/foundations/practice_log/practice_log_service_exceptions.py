"""Catch/wrap/log helpers for PracticeLogService.

Mirrors ConversationSessionServiceExceptions
(api/services/session_lifecycle/session_lifecycle_service_exceptions.py) --
catch each known leaf exception, wrap + log it, re-raise the wrapper.
Anything else falls through the final `except Exception` safety net.
"""

from typing import Callable, TypeVar

from api.models.foundations.practice_log.exceptions import (
    InvalidPracticeAttemptException,
    PracticeLogDependencyException,
    PracticeLogServiceException,
    PracticeLogUnavailableError,
    PracticeLogValidationException,
)

T = TypeVar("T")


class PracticeLogServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        try:
            return fn()
        except InvalidPracticeAttemptException as e:
            raise self._create_and_log_validation_exception(e) from e
        except PracticeLogUnavailableError as e:
            raise self._create_and_log_dependency_exception(e) from e
        except Exception as e:
            raise self._create_and_log_service_exception(e) from e

    def _create_and_log_validation_exception(self, exception: Exception) -> PracticeLogValidationException:
        validation_exception = PracticeLogValidationException(inner_exception=exception)
        self._logging_broker.log_error(validation_exception)
        return validation_exception

    def _create_and_log_dependency_exception(self, exception: Exception) -> PracticeLogDependencyException:
        dependency_exception = PracticeLogDependencyException(inner_exception=exception)
        self._logging_broker.log_error(dependency_exception)
        return dependency_exception

    def _create_and_log_service_exception(self, exception: Exception) -> PracticeLogServiceException:
        service_exception = PracticeLogServiceException(inner_exception=exception)
        self._logging_broker.log_error(service_exception)
        return service_exception
