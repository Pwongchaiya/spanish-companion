"""Catch/wrap/log helpers for HybridRetrievalOrchestrationService.

Mirrors NL.Core.Entitlements.Api/Services/Orchestrations/EntitlementCodes/
EntitlementCodesOrchestrationService.Exeptions.cs:19-135's TryCatch: catch
each known dependency exception, wrap + log it, re-raise the wrapper.
Anything else falls through the final `except Exception` safety net
(Exeptions.cs:77-85), matching the reference project's "nothing escapes
this service unwrapped" guarantee.

Three wrapper tiers, matching Review's:

1. Validation (Exeptions.cs:25-28 / CreateAndLogValidationException,
   Exeptions.cs:88-98). retrieve()'s two input checks -- blank query and
   top_k < 1 -- raise RetrievalValidationError from
   retrieval_service_validations.py, now called from *inside* _try_catch.
   Until H5 of the architecture conformance audit they raised a bare
   ValueError from outside it, on the argument that Review only ever passes
   a validated flag.corrected and the module-level RETRIEVAL_TOP_K so a bad
   input was a programming error. The untyped exception still had to land
   somewhere, and it landed in Review's catch-all and then an unmapped HTTP
   500 -- a 400 dressed as a server fault. Both this file and
   api/services/orchestrations/review/review_service_exceptions.py made that
   call; both were corrected together.
2. No DependencyValidation tier (Exeptions.cs:29-52 /
   CreateAndLogDependencyValidationException, Exeptions.cs:100-110). The
   Foundation-tier dependency exceptions caught below are infrastructure
   outages, not rejected inputs, so nothing validation-shaped would ever
   reach that tier. The Foundation services' *Validation* exceptions are
   deliberately NOT caught by name either: this service only ever passes a
   non-blank query and a top_k >= 1 down (guarded by tier 1 above), so a
   validation exception from beneath is a programming error and falls to
   the Service-tier safety net.

There is likewise no intermediate Failed*ServiceException before the
Service tier (Exeptions.cs:79-82) -- collapsed per
api/models/foundations/session_lifecycle/exceptions/session_service_exception.py:10-17.
"""

from typing import Callable, TypeVar

from rag.models.foundations.chunk_repository.exceptions import ChunkRepositoryDependencyException
from rag.models.foundations.embedding_model.exceptions import EmbeddingModelDependencyException
from rag.models.orchestrations.retrieval.exceptions import (
    RetrievalOrchestrationDependencyException,
    RetrievalOrchestrationServiceException,
    RetrievalOrchestrationValidationException,
    RetrievalValidationError,
)

T = TypeVar("T")


class HybridRetrievalOrchestrationServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        # Returns fn()'s value: retrieve() produces a List[ScoredChunk],
        # matching the reference's generic `ReturningXFunction` delegates
        # (Exeptions.cs:17-19).
        try:
            return fn()
        except RetrievalValidationError as e:
            raise self._create_and_log_validation_exception(e) from e
        except (EmbeddingModelDependencyException, ChunkRepositoryDependencyException) as e:
            raise self._create_and_log_dependency_exception(e) from e
        except Exception as e:
            raise self._create_and_log_service_exception(e) from e

    def _create_and_log_validation_exception(self, exception: Exception) -> RetrievalOrchestrationValidationException:
        """Mirrors CreateAndLogValidationException, Exeptions.cs:88-98.

        What arrives here is the RetrievalValidationError leaf itself, not a
        wrapper from a service beneath -- these checks are this service's own
        input validation. The leaf therefore sits one level in, at
        `.inner_exception`, where the dependency tier's sits two.
        """
        validation_exception = RetrievalOrchestrationValidationException(inner_exception=exception)
        self._logging_broker.log_error(validation_exception)
        return validation_exception

    def _create_and_log_dependency_exception(self, exception: Exception) -> RetrievalOrchestrationDependencyException:
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

    def _create_and_log_service_exception(self, exception: Exception) -> RetrievalOrchestrationServiceException:
        """Mirrors CreateAndLogServiceException, Exeptions.cs:124-134."""
        service_exception = RetrievalOrchestrationServiceException(inner_exception=exception)
        self._logging_broker.log_error(service_exception)
        return service_exception
