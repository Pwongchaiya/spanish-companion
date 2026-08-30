"""Catch/wrap/log helpers for FlagService.

Mirrors session_lifecycle_service_exceptions.py's TryCatch shape, but
`_try_catch` returns fn()'s value (mirrors review_service_exceptions.py's
`-> T` variant) since get_flag() produces a Flag rather than None.
"""

from typing import Callable, TypeVar

from api.models.flag.exceptions import (
    FlagDependencyException,
    FlagServiceException,
    FlagUnavailableError,
    FlagValidationException,
    NotFoundFlagException,
)

T = TypeVar("T")


class FlagServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        try:
            return fn()
        except NotFoundFlagException as e:
            raise self._create_and_log_validation_exception(e) from e
        except FlagUnavailableError as e:
            raise self._create_and_log_dependency_exception(e) from e
        except Exception as e:
            raise self._create_and_log_service_exception(e) from e

    def _create_and_log_validation_exception(self, exception: Exception) -> FlagValidationException:
        validation_exception = FlagValidationException(inner_exception=exception)
        self._logging_broker.log_error(validation_exception)
        return validation_exception

    def _create_and_log_dependency_exception(self, exception: Exception) -> FlagDependencyException:
        dependency_exception = FlagDependencyException(inner_exception=exception)
        self._logging_broker.log_error(dependency_exception)
        return dependency_exception

    def _create_and_log_service_exception(self, exception: Exception) -> FlagServiceException:
        service_exception = FlagServiceException(inner_exception=exception)
        self._logging_broker.log_error(service_exception)
        return service_exception
