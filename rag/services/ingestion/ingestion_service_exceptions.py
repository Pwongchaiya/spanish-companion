"""Catch/wrap/log helpers for IngestionService.

Mirrors NL.Core.Entitlements.Api/Services/Orchestrations/EntitlementCodes/
EntitlementCodesOrchestrationService.Exeptions.cs:19-135's TryCatch: catch
each known leaf exception, wrap + log it, re-raise the wrapper. Anything else
falls through the final `except Exception` safety net (Exeptions.cs:77-85),
matching the reference project's "nothing escapes this service unwrapped"
guarantee.

Three wrapper tiers, the same count Review settled on, because Ingestion has
the same two shapes of failure: a rejected input and an unreachable
dependency.

Cited omissions from the reference's tier set:

1. No DependencyValidation tier (Exeptions.cs:29-52 /
   CreateAndLogDependencyValidationException, Exeptions.cs:100-110).
   IngestionUnavailableError is an infrastructure outage, not a rejected
   input bubbled up from a service beneath — and there is no service beneath,
   only brokers (CLAUDE.md's ORC-002 waiver). Nothing validation-shaped could
   reach that tier.
2. No intermediate Failed*ServiceException before the catch-all
   (Exeptions.cs:79-82). Reasoning in
   rag/models/ingestion/exceptions/ingestion_orchestration_service_exception.py.

Before this rebuild `ingest_topic` had no TryCatch at all: it raised
IngestionValidationError bare and let every broker exception through raw.
"""

from typing import Callable, TypeVar

from rag.models.ingestion.exceptions import (
    IngestionOrchestrationDependencyException,
    IngestionOrchestrationServiceException,
    IngestionOrchestrationValidationException,
    IngestionUnavailableError,
    IngestionValidationError,
)

T = TypeVar("T")


class IngestionServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        # Generic return, like Review's `-> T` variant rather than Session
        # Lifecycle's `-> None`: ingest_topic produces an int row count,
        # matching the reference's generic `Returning<X>Function` delegates
        # (Exeptions.cs:17).
        try:
            return fn()
        except IngestionValidationError as e:
            raise self._create_and_log_validation_exception(e) from e
        except IngestionUnavailableError as e:
            raise self._create_and_log_dependency_exception(e) from e
        except Exception as e:
            raise self._create_and_log_service_exception(e) from e

    def _create_and_log_validation_exception(
        self, exception: Exception
    ) -> IngestionOrchestrationValidationException:
        """Mirrors CreateAndLogValidationException, Exeptions.cs:88-98."""
        validation_exception = IngestionOrchestrationValidationException(inner_exception=exception)
        self._logging_broker.log_error(validation_exception)
        return validation_exception

    def _create_and_log_dependency_exception(
        self, exception: Exception
    ) -> IngestionOrchestrationDependencyException:
        """Mirrors CreateAndLogDependencyException, Exeptions.cs:112-122.

        Cited divergence: the reference unwraps one level
        (`exception.InnerException as Xeption`, Exeptions.cs:117) because what
        it catches is itself already a wrapper from the Processing service
        beneath it. Ingestion catches IngestionUnavailableError directly — it
        IS the leaf — so it is carried through whole rather than unwrapped
        into None. Same divergence the Review rebuild recorded.
        """
        dependency_exception = IngestionOrchestrationDependencyException(inner_exception=exception)
        self._logging_broker.log_error(dependency_exception)
        return dependency_exception

    def _create_and_log_service_exception(
        self, exception: Exception
    ) -> IngestionOrchestrationServiceException:
        """Mirrors CreateAndLogServiceException, Exeptions.cs:124-134.

        Fed the raw Exception rather than a Failed*ServiceException wrapping
        it (Exeptions.cs:79-84) — the collapsed-tier divergence documented in
        ingestion_orchestration_service_exception.py.
        """
        service_exception = IngestionOrchestrationServiceException(inner_exception=exception)
        self._logging_broker.log_error(service_exception)
        return service_exception
