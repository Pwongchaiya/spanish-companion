"""Catch/wrap/log helpers for ReviewOrchestrator.

Mirrors NL.Core.Entitlements.Api/Services/Orchestrations/EntitlementCodes/
EntitlementCodesOrchestrationService.Exeptions.cs:19-135's TryCatch: catch
each known leaf/dependency exception, wrap + log it, re-raise the wrapper.
Anything else falls through the final `except Exception` safety net
(Exeptions.cs:77-85), matching the reference project's "nothing escapes
this service unwrapped" guarantee.

Three wrapper tiers, one more than Session Lifecycle collapsed to, because
Review has a genuine dependency-failure category that Session Lifecycle
lacks: RetrievalUnavailableError from RetrievalController.retrieve()
(rag/services/retrieval/service.py:76-84).

Two cited omissions from the reference's tier set:

1. No DependencyValidation tier (Exeptions.cs:29-52 /
   CreateAndLogDependencyValidationException, Exeptions.cs:100-110).
   RetrievalUnavailableError is an infrastructure outage, not a rejected
   input, so nothing validation-shaped would ever reach that tier.
2. No Generation dependency catch. GenerationError is handled inside
   GenerationService.explain() (rag/services/generation.py:37-46) and
   replaced with a fallback string; it never propagates to
   GenerationController.explain() or here.

`retrieve()`'s other documented raise, a bare ValueError for blank query or
top_k < 1, is deliberately left to the final `except Exception` catch-all
rather than given its own tier: Review only ever passes it a validated
flag.corrected and the module-level RETRIEVAL_TOP_K, so a ValueError from
there is a programming error, not an expected condition.
"""

from typing import Callable, TypeVar

from api.models.review.exceptions import (
    FailedReviewOrchestrationServiceException,
    InvalidReviewOrchestrationException,
    NotFoundFlagException,
    ReviewOrchestrationDependencyException,
    ReviewOrchestrationServiceException,
    ReviewOrchestrationValidationException,
)
from rag.services.retrieval.service import RetrievalUnavailableError

T = TypeVar("T")


class ReviewOrchestratorExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        # Returns fn()'s value, unlike Session Lifecycle's `-> None` variant:
        # Review's wrapped methods produce an Explanation / PracticeAttempt,
        # matching the reference's generic `ReturningXFunction` delegates.
        try:
            return fn()
        except InvalidReviewOrchestrationException as e:
            raise self._create_and_log_validation_exception(e) from e
        except NotFoundFlagException as e:
            raise self._create_and_log_validation_exception(e) from e
        except RetrievalUnavailableError as e:
            raise self._create_and_log_dependency_exception(e) from e
        except Exception as e:
            failed = FailedReviewOrchestrationServiceException(inner_exception=e)
            raise self._create_and_log_service_exception(failed) from e

    def _create_and_log_validation_exception(
        self, exception: Exception
    ) -> ReviewOrchestrationValidationException:
        """Mirrors CreateAndLogValidationException, Exeptions.cs:88-98."""
        validation_exception = ReviewOrchestrationValidationException(inner_exception=exception)
        self._logging_broker.log_error(validation_exception)
        return validation_exception

    def _create_and_log_dependency_exception(
        self, exception: Exception
    ) -> ReviewOrchestrationDependencyException:
        """Mirrors CreateAndLogDependencyException, Exeptions.cs:112-122.

        Cited divergence: the reference unwraps one level
        (`exception.InnerException as Xeption`, Exeptions.cs:117) because
        what it catches is itself already a wrapper from the Processing
        service beneath it. Review catches RetrievalUnavailableError
        directly -- it IS the leaf -- so it is carried through whole rather
        than unwrapped into None.
        """
        dependency_exception = ReviewOrchestrationDependencyException(inner_exception=exception)
        self._logging_broker.log_error(dependency_exception)
        return dependency_exception

    def _create_and_log_service_exception(
        self, exception: Exception
    ) -> ReviewOrchestrationServiceException:
        """Mirrors CreateAndLogServiceException, Exeptions.cs:124-134."""
        service_exception = ReviewOrchestrationServiceException(inner_exception=exception)
        self._logging_broker.log_error(service_exception)
        return service_exception
