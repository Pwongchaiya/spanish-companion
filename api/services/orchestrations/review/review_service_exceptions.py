"""Catch/wrap/log helpers for ReviewOrchestrator.

Mirrors NL.Core.Entitlements.Api/Services/Orchestrations/EntitlementCodes/
EntitlementCodesOrchestrationService.Exeptions.cs:19-135's TryCatch: catch
each known leaf/dependency exception, wrap + log it, re-raise the wrapper.
Anything else falls through the final `except Exception` safety net
(Exeptions.cs:77-85), matching the reference project's "nothing escapes
this service unwrapped" guarantee.

Three wrapper tiers, one more than Session Lifecycle collapsed to, because
Review has a genuine dependency-failure category that Session Lifecycle
lacks: RetrievalOrchestrationDependencyException from
HybridRetrievalService.retrieve().

The validation tier catches the *wrappers* the services beneath raise --
FlagValidationException (holding NotFoundFlagException),
PracticeLogValidationException (holding InvalidPracticeAttemptException),
and RetrievalOrchestrationValidationException (holding
RetrievalValidationError) -- never their raw leaves, the same shape already used here for
RetrievalOrchestrationDependencyException and one tier down in
IngestionServiceExceptions. Consequence: those leaves now sit at
`.inner_exception.inner_exception` on the ReviewOrchestrationValidationException,
one level deeper than before.

Two cited omissions from the reference's tier set:

1. No DependencyValidation tier (Exeptions.cs:29-52 /
   CreateAndLogDependencyValidationException, Exeptions.cs:100-110).
   Retrieval's dependency failure is an infrastructure outage, not a
   rejected input, so nothing validation-shaped would ever reach that tier.
   FlagDependencyException / PracticeLogDependencyException are likewise not
   caught: those are infrastructure outages too, and fall to the catch-all
   service tier rather than being mislabelled as Retrieval-shaped.
2. No Generation dependency catch. GenerationError is handled inside
   GenerationService.explain() and replaced with a fallback string; it never
   propagates here.

`retrieve()`'s blank-query / top_k < 1 rejection used to be a bare
ValueError, deliberately left to the final `except Exception` catch-all on
the argument that Review only ever passes a validated flag.corrected and the
module-level RETRIEVAL_TOP_K. H5 of the architecture conformance audit
overturned that: the catch-all made the route answer 500 for what is a 400.
Retrieval now raises RetrievalOrchestrationValidationException and it is
caught by name in the validation tier above.
"""

from typing import Callable, TypeVar

from api.models.flag.exceptions import FlagValidationException
from api.models.practice_log.exceptions import PracticeLogValidationException
from api.models.review.exceptions import (
    FailedReviewOrchestrationServiceException,
    ReviewOrchestrationDependencyException,
    ReviewOrchestrationServiceException,
    ReviewOrchestrationValidationException,
)
from rag.models.retrieval.exceptions import (
    RetrievalOrchestrationDependencyException,
    RetrievalOrchestrationValidationException,
)

T = TypeVar("T")


class ReviewOrchestratorExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        # Returns fn()'s value, unlike Session Lifecycle's `-> None` variant:
        # Review's wrapped methods produce an Explanation / PracticeAttempt,
        # matching the reference's generic `ReturningXFunction` delegates.
        try:
            return fn()
        except FlagValidationException as e:
            raise self._create_and_log_validation_exception(e) from e
        except PracticeLogValidationException as e:
            raise self._create_and_log_validation_exception(e) from e
        except RetrievalOrchestrationValidationException as e:
            raise self._create_and_log_validation_exception(e) from e
        except RetrievalOrchestrationDependencyException as e:
            raise self._create_and_log_dependency_exception(e) from e
        except Exception as e:
            failed = FailedReviewOrchestrationServiceException(inner_exception=e)
            raise self._create_and_log_service_exception(failed) from e

    def _create_and_log_validation_exception(
        self, exception: Exception
    ) -> ReviewOrchestrationValidationException:
        """Mirrors CreateAndLogValidationException, Exeptions.cs:88-98.

        What arrives here is FlagValidationException,
        PracticeLogValidationException, or
        RetrievalOrchestrationValidationException -- the wrapper raised by
        the service beneath, carried through whole rather than unwrapped (Exeptions.cs:117's
        divergence, the same call made below for the dependency tier). The
        leaf stays reachable as `.inner_exception.inner_exception`.
        """
        validation_exception = ReviewOrchestrationValidationException(inner_exception=exception)
        self._logging_broker.log_error(validation_exception)
        return validation_exception

    def _create_and_log_dependency_exception(
        self, exception: Exception
    ) -> ReviewOrchestrationDependencyException:
        """Mirrors CreateAndLogDependencyException, Exeptions.cs:112-122.

        What arrives here is RetrievalOrchestrationDependencyException --
        already wrapped by Retrieval's own Orchestration tier
        (rag/services/retrieval/retrieval_service_exceptions.py), which is
        what holds the RetrievalUnavailableError leaf. That is the
        reference's own cross-service shape, Exeptions.cs:53-76: the outer
        service catches the *wrapper* types the service beneath it raises,
        never that service's raw leaves.

        Cited divergence retained from the reference: it unwraps one level
        (`exception.InnerException as Xeption`, Exeptions.cs:117). Review
        carries the wrapper through whole instead, so the leaf stays
        reachable as `.inner_exception.inner_exception` rather than being
        flattened -- same call already made for
        FailedReviewOrchestrationServiceException.
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
