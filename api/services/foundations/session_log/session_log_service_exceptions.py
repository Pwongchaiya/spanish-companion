"""Catch/wrap/log helpers for SessionLogService.

Mirrors flag_service_exceptions.py's TryCatch shape, with `_try_catch`
returning fn()'s value since save() produces an Optional[Path]. Two wrapper
tiers, not three: nothing here is validation-shaped (see the base class's
docstring), so there is no validation branch to add.
"""

from typing import Callable, TypeVar

from api.models.session_log.exceptions import (
    SessionLogDependencyException,
    SessionLogServiceException,
    SessionLogUnavailableError,
)

T = TypeVar("T")


class SessionLogServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        try:
            return fn()
        except SessionLogUnavailableError as e:
            raise self._create_and_log_dependency_exception(e) from e
        except Exception as e:
            raise self._create_and_log_service_exception(e) from e

    def _create_and_log_dependency_exception(self, exception: Exception) -> SessionLogDependencyException:
        dependency_exception = SessionLogDependencyException(inner_exception=exception)
        self._logging_broker.log_error(dependency_exception)
        return dependency_exception

    def _create_and_log_service_exception(self, exception: Exception) -> SessionLogServiceException:
        service_exception = SessionLogServiceException(inner_exception=exception)
        self._logging_broker.log_error(service_exception)
        return service_exception
