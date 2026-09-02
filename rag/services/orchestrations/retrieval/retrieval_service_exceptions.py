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
   CreateAndLogDependencyValidationException, Exeptions.cs:100-110). The
   Foundation-tier dependency exceptions caught below are infrastructure
   outages, not rejected inputs, so nothing validation-shaped would ever
   reach that tier. The Foundation services' *Validation* exceptions are
   deliberately NOT caught by name either: this service only ever passes a
   non-blank query (guarded above _try_catch) and a top_k >= 1 down, so a
   validation exception from beneath is a programming error and falls to
   the Service-tier safety net.

There is likewise no intermediate Failed*ServiceException before the
Service tier (Exeptions.cs:79-82) -- collapsed per
api/models/session_lifecycle/exceptions/session_service_exception.py:10-17.
"""

from typing import Callable, TypeVar

from rag.models.chunk_repository.exceptions import ChunkRepositoryDependencyException
from rag.models.embedding_model.exceptions import EmbeddingModelDependencyException
from rag.models.retrieval.exceptions import (
    RetrievalOrchestrationDependencyException,
    RetrievalOrchestrationServiceException,
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
        except (EmbeddingModelDependencyException, ChunkRepositoryDependencyException) as e:
            raise self._create_and_log_dependency_exception(e) from e
        except Exception as e:
            raise self._create_and_log_service_exception(e) from e

    def _create_and_log_dependency_exception(
        self, exception: Exception
    ) -> RetrievalOrchestrationDependencyException:
        """Mirrors CreateAndLogDependencyException, Exeptions.cs:112-122.

        What arrives here is EmbeddingModelDependencyException or
        ChunkRepositoryDependencyException -- already wrapped by the
        Foundation service beneath, which is what holds the raw
        EmbeddingModelUnavailableError / ChunkRepositoryUnavailableError
        leaf. That is the reference's own cross-service shape,
        Exeptions.cs:53-76: the outer service catches the *wrapper* types
        the service beneath it raises, never that service's raw leaves.

        Cited divergence retained from the reference: it unwraps one level
        (`exception.InnerException as Xeption`, Exeptions.cs:117). Retrieval
        carries the wrapper through whole instead, so the leaf stays
        reachable as `.inner_exception.inner_exception` rather than being
        flattened -- the same call api/services/review/
        review_service_exceptions.py already makes one layer up. The wrapper
        type this returns is unchanged (Review still catches
        RetrievalOrchestrationDependencyException by name); only the inner
        leaf it carries is different.
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
