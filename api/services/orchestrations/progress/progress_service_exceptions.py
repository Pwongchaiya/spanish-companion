"""Catch/wrap/log helpers for ProgressOrchestrationService.

Mirrors LearnerProfileOrchestrationServiceExceptions's shape
(learner_profile_orchestration_service_exceptions.py): catch each known
leaf-wrapper, wrap + log it, re-raise. Three tiers -- Validation, Dependency,
catch-all Service (via the Failed* intermediate) -- because both
dependencies here (LearnerProfile Processing, MistakePattern/TopicCovered
Foundation) raise from that same three-shape vocabulary.

Validation tier catches the *wrappers* LearnerProfileProcessingService /
IMistakePatternService / ITopicCoveredService / ISessionLogEntryService
raise --
LearnerProfileValidationException, MistakePatternValidationException,
TopicCoveredValidationException, SessionLogEntryValidationException --
never their raw leaves, same shape as
LearnerProfile's orchestration service. The leaf stays reachable at
`.inner_exception.inner_exception`.
"""

from typing import Callable, TypeVar

from api.models.foundations.learner_profile.exceptions import (
    LearnerProfileDependencyException,
    LearnerProfileValidationException,
)
from api.models.foundations.mistake_pattern.exceptions import (
    MistakePatternDependencyException,
    MistakePatternValidationException,
)
from api.models.foundations.pronunciation_result.exceptions import (
    PronunciationResultDependencyException,
    PronunciationResultValidationException,
)
from api.models.foundations.session_log_entry.exceptions import (
    SessionLogEntryDependencyException,
    SessionLogEntryValidationException,
)
from api.models.foundations.topic_covered.exceptions import (
    TopicCoveredDependencyException,
    TopicCoveredValidationException,
)
from api.models.orchestrations.progress.exceptions import (
    FailedProgressOrchestrationServiceException,
    ProgressOrchestrationDependencyException,
    ProgressOrchestrationServiceException,
    ProgressOrchestrationValidationException,
)

T = TypeVar("T")


class ProgressOrchestrationServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        try:
            return fn()
        except (
            LearnerProfileValidationException,
            MistakePatternValidationException,
            TopicCoveredValidationException,
            SessionLogEntryValidationException,
            PronunciationResultValidationException,
        ) as e:
            raise self._create_and_log_validation_exception(e) from e
        except (
            LearnerProfileDependencyException,
            MistakePatternDependencyException,
            TopicCoveredDependencyException,
            SessionLogEntryDependencyException,
            PronunciationResultDependencyException,
        ) as e:
            raise self._create_and_log_dependency_exception(e) from e
        except Exception as e:
            failed = FailedProgressOrchestrationServiceException(inner_exception=e)
            raise self._create_and_log_service_exception(failed) from e

    def _create_and_log_validation_exception(self, exception: Exception) -> ProgressOrchestrationValidationException:
        validation_exception = ProgressOrchestrationValidationException(inner_exception=exception)
        self._logging_broker.log_error(validation_exception)
        return validation_exception

    def _create_and_log_dependency_exception(self, exception: Exception) -> ProgressOrchestrationDependencyException:
        dependency_exception = ProgressOrchestrationDependencyException(inner_exception=exception)
        self._logging_broker.log_error(dependency_exception)
        return dependency_exception

    def _create_and_log_service_exception(self, exception: Exception) -> ProgressOrchestrationServiceException:
        service_exception = ProgressOrchestrationServiceException(inner_exception=exception)
        self._logging_broker.log_error(service_exception)
        return service_exception
