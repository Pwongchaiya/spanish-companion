"""Catch/wrap/log helpers for SessionRecapAggregationService.

Mirrors ProgressOrchestrationServiceExceptions's shape (single dependency's
Validation/Dependency tiers caught by name, everything else -- including the
dependency's own catch-all ServiceException, and Review's
ReviewOrchestrationServiceException, which has no Validation/Dependency tier
for list_flags() to begin with -- falls to the generic Exception catch-all).
"""

from typing import Callable, TypeVar

from api.models.aggregations.session_recap.exceptions import (
    FailedSessionRecapAggregationServiceException,
    SessionRecapAggregationDependencyException,
    SessionRecapAggregationServiceException,
    SessionRecapAggregationValidationException,
)
from api.models.orchestrations.progress.exceptions import (
    ProgressOrchestrationDependencyException,
    ProgressOrchestrationValidationException,
)

T = TypeVar("T")


class SessionRecapAggregationServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        try:
            return fn()
        except ProgressOrchestrationValidationException as e:
            raise self._create_and_log_validation_exception(e) from e
        except ProgressOrchestrationDependencyException as e:
            raise self._create_and_log_dependency_exception(e) from e
        except Exception as e:
            failed = FailedSessionRecapAggregationServiceException(inner_exception=e)
            raise self._create_and_log_service_exception(failed) from e

    def _create_and_log_validation_exception(
        self, exception: Exception
    ) -> SessionRecapAggregationValidationException:
        validation_exception = SessionRecapAggregationValidationException(inner_exception=exception)
        self._logging_broker.log_error(validation_exception)
        return validation_exception

    def _create_and_log_dependency_exception(
        self, exception: Exception
    ) -> SessionRecapAggregationDependencyException:
        dependency_exception = SessionRecapAggregationDependencyException(inner_exception=exception)
        self._logging_broker.log_error(dependency_exception)
        return dependency_exception

    def _create_and_log_service_exception(self, exception: Exception) -> SessionRecapAggregationServiceException:
        service_exception = SessionRecapAggregationServiceException(inner_exception=exception)
        self._logging_broker.log_error(service_exception)
        return service_exception
