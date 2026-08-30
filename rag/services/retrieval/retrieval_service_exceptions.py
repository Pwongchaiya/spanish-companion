"""Catch/wrap/log helpers for HybridRetrievalService.

Mirrors NL.Core.Entitlements.Api/Services/Orchestrations/EntitlementCodes/
EntitlementCodesOrchestrationService.Exeptions.cs:19-135's TryCatch: catch
each known dependency exception, wrap + log it, re-raise the wrapper.
Anything else falls through the final `except Exception` safety net
(Exeptions.cs:77-85), matching the reference project's "nothing escapes
this service unwrapped" guarantee.

Two wrapper tiers, one fewer than Review's three, because Retrieval has no
validation-shaped failure to carry:

1. No Validation tier (Exeptions.cs:25-28 / CreateAndLogValidationException,
   Exeptions.cs:88-98). retrieve()'s only input checks -- blank query and
   top_k < 1 -- raise a bare ValueError from *outside* _try_catch, so they
   propagate completely raw. Review only ever passes a validated
   flag.corrected and the module-level RETRIEVAL_TOP_K, so a ValueError from
   there is a programming error, not an expected condition. This is the same
   call that api/services/review/review_service_exceptions.py already made
   about this exact ValueError; the rebuild preserves it verbatim rather
   than inventing a Validation tier for it.
2. No DependencyValidation tier (Exeptions.cs:29-52 /
   CreateAndLogDependencyValidationException, Exeptions.cs:100-110).
   RetrievalUnavailableError is an infrastructure outage, not a rejected
   input, so nothing validation-shaped would ever reach that tier.

There is likewise no intermediate Failed*ServiceException before the
Service tier (Exeptions.cs:79-82) -- collapsed per
api/models/session_lifecycle/exceptions/session_service_exception.py:10-17.
"""

from typing import Callable, TypeVar

from rag.models.retrieval.exceptions import (
    RetrievalOrchestrationDependencyException,
    RetrievalOrchestrationServiceException,
    RetrievalUnavailableError,
)

T = TypeVar("T")


class HybridRetrievalServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        # Returns fn()'s value: retrieve() produces a List[ScoredChunk],
        # matching the reference's generic `ReturningXFunction` delegates
        # (Exeptions.cs:17-19).
        try:
            return fn()
        except RetrievalUnavailableError as e:
            raise self._create_and_log_dependency_exception(e) from e
        except Exception as e:
            raise self._create_and_log_service_exception(e) from e

    def _create_and_log_dependency_exception(
        self, exception: Exception
    ) -> RetrievalOrchestrationDependencyException:
        """Mirrors CreateAndLogDependencyException, Exeptions.cs:112-122.

        Cited divergence: the reference unwraps one level
        (`exception.InnerException as Xeption`, Exeptions.cs:117) because
        what it catches is itself already a wrapper from the Processing
        service beneath it. Retrieval catches RetrievalUnavailableError
        directly -- it IS the leaf, and there is no layer beneath it here --
        so it is carried through whole rather than unwrapped into None.
        """
        dependency_exception = RetrievalOrchestrationDependencyException(inner_exception=exception)
        self._logging_broker.log_error(dependency_exception)
        return dependency_exception

    def _create_and_log_service_exception(
        self, exception: Exception
    ) -> RetrievalOrchestrationServiceException:
        """Mirrors CreateAndLogServiceException, Exeptions.cs:124-134."""
        service_exception = RetrievalOrchestrationServiceException(inner_exception=exception)
        self._logging_broker.log_error(service_exception)
        return service_exception
