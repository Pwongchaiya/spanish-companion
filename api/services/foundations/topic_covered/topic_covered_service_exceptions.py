"""Catch/wrap/log helpers for TopicCoveredService.

Mirrors LearnerProfileServiceExceptions's shape: `_try_catch` returns
fn()'s value since every public method here produces a TopicCovered or a
list[TopicCovered].
"""

from typing import Callable, TypeVar

from api.models.foundations.topic_covered.exceptions import (
    InvalidTopicCoveredInputError,
    TopicCoveredDependencyException,
    TopicCoveredServiceException,
    TopicCoveredUnavailableError,
    TopicCoveredValidationException,
)

T = TypeVar("T")


class TopicCoveredServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        try:
            return fn()
        except InvalidTopicCoveredInputError as e:
            raise self._create_and_log_validation_exception(e) from e
        except TopicCoveredUnavailableError as e:
            raise self._create_and_log_dependency_exception(e) from e
        except Exception as e:
            raise self._create_and_log_service_exception(e) from e

    def _create_and_log_validation_exception(self, exception: Exception) -> TopicCoveredValidationException:
        validation_exception = TopicCoveredValidationException(inner_exception=exception)
        self._logging_broker.log_error(validation_exception)
        return validation_exception

    def _create_and_log_dependency_exception(self, exception: Exception) -> TopicCoveredDependencyException:
        dependency_exception = TopicCoveredDependencyException(inner_exception=exception)
        self._logging_broker.log_error(dependency_exception)
        return dependency_exception

    def _create_and_log_service_exception(self, exception: Exception) -> TopicCoveredServiceException:
        service_exception = TopicCoveredServiceException(inner_exception=exception)
        self._logging_broker.log_error(service_exception)
        return service_exception
