"""Exposure-tier exception wrapping a failed dependency call."""

from api.errors import ApiError


class ReviewOrchestrationDependencyException(ApiError):
    """Wraps a dependency failure raised by one of Review's rag dependencies.

    Mirrors NL.Core.Entitlements.Api/Models/Orchestrations/EntitlementCodes/
    EntitlementCodeOrchestrationDependencyException.cs:11-13, produced by
    CreateAndLogDependencyException
    (EntitlementCodesOrchestrationService.Exeptions.cs:112-122).

    In practice it wraps exactly one thing today:
    `RetrievalUnavailableError` from RetrievalController.retrieve()
    (rag/services/retrieval/service.py:76-84) -- the chunk store or
    embedding model being unreachable.

    Two deliberate, cited divergences from the reference's tier set:

    1. No DependencyValidation tier. The reference pairs every Dependency
       tier with a DependencyValidation one
       (EntitlementCodeOrchestrationDependencyValidationException.cs, fed by
       Exeptions.cs:29-52). Review's only dependency failure mode,
       RetrievalUnavailableError, is an infrastructure outage rather than a
       rejected input, so there is nothing validation-shaped for that tier
       to carry. Same reasoning style as Session Lifecycle's "no Dependency
       tier was added" note, applied one tier down.

    2. Nothing is wrapped for Generation. GenerationError is caught *inside*
       GenerationService.explain() (rag/services/generation.py:37-46) and
       replaced with a fallback string, so it never reaches
       GenerationController.explain() or this service. There is no
       Generation dependency exception for Review to catch.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Review dependency error occurred. Contact support.",
            inner_exception=inner_exception,
        )
