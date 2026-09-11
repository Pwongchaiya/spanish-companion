"""Catch/wrap/log helpers for MistakePatternService.

Mirrors LearnerProfileServiceExceptions's shape: `_try_catch` returns
fn()'s value since every public method here produces a MistakePattern or a
list of them.
"""

from typing import Callable, TypeVar

from api.models.foundations.mistake_pattern.exceptions import (
    InvalidMistakePatternInputError,
    MistakePatternDependencyException,
    MistakePatternServiceException,
    MistakePatternUnavailableError,
    MistakePatternValidationException,
    NotFoundMistakePatternException,
)

T = TypeVar("T")


class MistakePatternServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        try:
            return fn()
        except InvalidMistakePatternInputError as e:
            raise self._create_and_log_validation_exception(e) from e
        except NotFoundMistakePatternException as e:
            raise self._create_and_log_validation_exception(e) from e
        except MistakePatternUnavailableError as e:
            raise self._create_and_log_dependency_exception(e) from e
        except Exception as e:
            raise self._create_and_log_service_exception(e) from e

    def _create_and_log_validation_exception(self, exception: Exception) -> MistakePatternValidationException:
        validation_exception = MistakePatternValidationException(inner_exception=exception)
        self._logging_broker.log_error(validation_exception)
        return validation_exception

    def _create_and_log_dependency_exception(self, exception: Exception) -> MistakePatternDependencyException:
        dependency_exception = MistakePatternDependencyException(inner_exception=exception)
        self._logging_broker.log_error(dependency_exception)
        return dependency_exception

    def _create_and_log_service_exception(self, exception: Exception) -> MistakePatternServiceException:
        service_exception = MistakePatternServiceException(inner_exception=exception)
        self._logging_broker.log_error(service_exception)
        return service_exception
