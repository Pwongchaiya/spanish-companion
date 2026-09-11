"""Catch/wrap/log helpers for LearnerProfileService.

Mirrors FlagServiceExceptions's shape: `_try_catch` returns fn()'s value
since every public method here produces a LearnerProfile.
"""

from typing import Callable, TypeVar

from api.models.foundations.learner_profile.exceptions import (
    InvalidLearnerProfileInputError,
    LearnerProfileDependencyException,
    LearnerProfileServiceException,
    LearnerProfileUnavailableError,
    LearnerProfileValidationException,
    NotFoundLearnerProfileException,
)

T = TypeVar("T")


class LearnerProfileServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        try:
            return fn()
        except InvalidLearnerProfileInputError as e:
            raise self._create_and_log_validation_exception(e) from e
        except NotFoundLearnerProfileException as e:
            raise self._create_and_log_validation_exception(e) from e
        except LearnerProfileUnavailableError as e:
            raise self._create_and_log_dependency_exception(e) from e
        except Exception as e:
            raise self._create_and_log_service_exception(e) from e

    def _create_and_log_validation_exception(self, exception: Exception) -> LearnerProfileValidationException:
        validation_exception = LearnerProfileValidationException(inner_exception=exception)
        self._logging_broker.log_error(validation_exception)
        return validation_exception

    def _create_and_log_dependency_exception(self, exception: Exception) -> LearnerProfileDependencyException:
        dependency_exception = LearnerProfileDependencyException(inner_exception=exception)
        self._logging_broker.log_error(dependency_exception)
        return dependency_exception

    def _create_and_log_service_exception(self, exception: Exception) -> LearnerProfileServiceException:
        service_exception = LearnerProfileServiceException(inner_exception=exception)
        self._logging_broker.log_error(service_exception)
        return service_exception
