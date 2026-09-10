"""Exposure-tier exception wrapping a validation-tier leaf exception."""

from rag.errors import RagError


class RetrievalOrchestrationValidationException(RagError):
    """Wraps RetrievalValidationError for consumers, without leaking internals.

    Mirrors NL.Core.Entitlements.Api/Models/Orchestrations/EntitlementCodes/
    EntitlementCodeOrchestrationValidationException.cs:11-13 -- message +
    innerException, produced by CreateAndLogValidationException
    (EntitlementCodesOrchestrationService.Exeptions.cs:88-98).

    Only one leaf lands here (RetrievalValidationError), so unlike Review --
    which needs an `isinstance(e.inner_exception, NotFoundFlagException)`
    filter to tell its two leaves apart -- no consumer-side discrimination
    is required.

    ReviewOrchestrationService catches this type by name and re-wraps it into
    ReviewOrchestrationValidationException, which api/exposers/review.py
    already maps to 400. From the route's side the leaf therefore sits at
    `.inner_exception.inner_exception`, the same depth as Review's own
    Foundation-tier leaves.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Retrieval validation error occurred. Fix the errors and try again.",
            inner_exception,
        )
