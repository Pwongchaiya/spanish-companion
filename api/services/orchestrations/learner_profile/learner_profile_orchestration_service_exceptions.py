"""Catch/wrap/log helpers for LearnerProfileOrchestrationService.

Mirrors ReviewOrchestrationServiceExceptions's shape (review_service_exceptions.py):
catch each known leaf-wrapper, wrap + log it, re-raise. Three tiers, same as
Review -- Validation, Dependency, catch-all Service (via the Failed*
intermediate) -- because all four dependencies here (LearnerProfile
Processing, MistakePattern/TopicCovered/Flag Foundation) raise from that
same three-shape vocabulary; there is no fourth failure category the way
Review's rag dependency added one.

Validation tier catches the *wrappers* LearnerProfileProcessingService /
IMistakePatternService / ITopicCoveredService raise --
LearnerProfileValidationException, MistakePatternValidationException,
TopicCoveredValidationException -- never their raw leaves, same shape as
Review. The leaf stays reachable at `.inner_exception.inner_exception`.

FlagService.list_flags() raises nothing (see i_flag_service.py's docstring:
a missing/corrupt flag file returns [] as a normal state), so there is no
Flag-shaped exception for either tier to catch -- Flag simply never
contributes a leaf here, the same absence Review notes for Generation.

Each of the three Foundation/Processing *ServiceException classes
(LearnerProfileServiceException, MistakePatternServiceException,
TopicCoveredServiceException) is deliberately NOT caught by name -- same
precedent as Review not catching Flag/PracticeLog's own *ServiceException.
All three fall to the final `except Exception` catch-all below.
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
from api.models.foundations.topic_covered.exceptions import (
    TopicCoveredDependencyException,
    TopicCoveredValidationException,
)
from api.models.orchestrations.learner_profile.exceptions import (
    FailedLearnerProfileOrchestrationServiceException,
    LearnerProfileOrchestrationDependencyException,
    LearnerProfileOrchestrationServiceException,
    LearnerProfileOrchestrationValidationException,
)

T = TypeVar("T")


class LearnerProfileOrchestrationServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        try:
            return fn()
        except (
            LearnerProfileValidationException,
            MistakePatternValidationException,
            TopicCoveredValidationException,
        ) as e:
            raise self._create_and_log_validation_exception(e) from e
        except (
            LearnerProfileDependencyException,
            MistakePatternDependencyException,
            TopicCoveredDependencyException,
        ) as e:
            raise self._create_and_log_dependency_exception(e) from e
        except Exception as e:
            failed = FailedLearnerProfileOrchestrationServiceException(inner_exception=e)
            raise self._create_and_log_service_exception(failed) from e

    def _create_and_log_validation_exception(
        self, exception: Exception
    ) -> LearnerProfileOrchestrationValidationException:
        validation_exception = LearnerProfileOrchestrationValidationException(inner_exception=exception)
        self._logging_broker.log_error(validation_exception)
        return validation_exception

    def _create_and_log_dependency_exception(
        self, exception: Exception
    ) -> LearnerProfileOrchestrationDependencyException:
        dependency_exception = LearnerProfileOrchestrationDependencyException(inner_exception=exception)
        self._logging_broker.log_error(dependency_exception)
        return dependency_exception

    def _create_and_log_service_exception(self, exception: Exception) -> LearnerProfileOrchestrationServiceException:
        service_exception = LearnerProfileOrchestrationServiceException(inner_exception=exception)
        self._logging_broker.log_error(service_exception)
        return service_exception
