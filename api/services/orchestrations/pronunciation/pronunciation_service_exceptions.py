"""Catch/wrap/log helpers for PronunciationOrchestrationService.

Same three-tier shape as ReviewOrchestrationServiceExceptions
(api/services/orchestrations/review/review_service_exceptions.py:57-124):
catch each known wrapper the Foundation services beneath raise, wrap + log,
re-raise; anything else goes through the Failed* intermediate to the
catch-all service tier.

Deliberate choice: PronunciationResultValidationException is NOT caught by
the validation tier. Its input is built here from an assessment Azure already
scored, never from the caller, so a rejection there is a server-side bug --
it falls to the service tier (500), not a misleading 400.
"""

from typing import Callable, TypeVar

from api.models.foundations.pronunciation_assessment.exceptions import (
    PronunciationAssessmentDependencyException,
    PronunciationAssessmentValidationException,
)
from api.models.foundations.pronunciation_result.exceptions import PronunciationResultDependencyException
from api.models.orchestrations.pronunciation.exceptions import (
    FailedPronunciationOrchestrationServiceException,
    PronunciationOrchestrationDependencyException,
    PronunciationOrchestrationServiceException,
    PronunciationOrchestrationValidationException,
)

T = TypeVar("T")


class PronunciationOrchestrationServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        try:
            return fn()
        except PronunciationAssessmentValidationException as e:
            raise self._create_and_log_validation_exception(e) from e
        except (PronunciationAssessmentDependencyException, PronunciationResultDependencyException) as e:
            raise self._create_and_log_dependency_exception(e) from e
        except Exception as e:
            failed = FailedPronunciationOrchestrationServiceException(inner_exception=e)
            raise self._create_and_log_service_exception(failed) from e

    def _create_and_log_validation_exception(
        self, exception: Exception
    ) -> PronunciationOrchestrationValidationException:
        validation_exception = PronunciationOrchestrationValidationException(inner_exception=exception)
        self._logging_broker.log_error(validation_exception)
        return validation_exception

    def _create_and_log_dependency_exception(
        self, exception: Exception
    ) -> PronunciationOrchestrationDependencyException:
        dependency_exception = PronunciationOrchestrationDependencyException(inner_exception=exception)
        self._logging_broker.log_error(dependency_exception)
        return dependency_exception

    def _create_and_log_service_exception(self, exception: Exception) -> PronunciationOrchestrationServiceException:
        service_exception = PronunciationOrchestrationServiceException(inner_exception=exception)
        self._logging_broker.log_error(service_exception)
        return service_exception
