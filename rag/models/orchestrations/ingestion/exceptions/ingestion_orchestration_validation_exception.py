"""Exposure-tier exception wrapping a validation-tier leaf exception."""

from rag.errors import RagError


class IngestionOrchestrationValidationException(RagError):
    """Wraps IngestionValidationError for consumers, without leaking internals.

    Mirrors NL.Core.Entitlements.Api/Models/Orchestrations/EntitlementCodes/
    EntitlementCodeOrchestrationValidationException.cs:11-13 -- message +
    innerException, produced by CreateAndLogValidationException
    (EntitlementCodesOrchestrationService.Exeptions.cs:88-98).

    Only one leaf lands here (IngestionValidationError), so unlike Review --
    which needs an `isinstance(e.inner_exception, NotFoundFlagException)`
    filter to tell its two leaves apart -- no consumer-side discrimination
    is required.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Ingestion validation error occurred. Fix the errors and try again.",
            inner_exception,
        )
