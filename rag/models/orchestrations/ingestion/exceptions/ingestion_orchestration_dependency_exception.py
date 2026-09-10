"""Exposure-tier exception wrapping a failed dependency call."""

from rag.errors import RagError


class IngestionOrchestrationDependencyException(RagError):
    """Wraps ChunkRepositoryDependencyException / EmbeddingModelDependencyException
    -- a Foundation service Ingestion depends on failed.

    Mirrors NL.Core.Entitlements.Api/Models/Orchestrations/EntitlementCodes/
    EntitlementCodeOrchestrationDependencyException.cs:11-13, produced by
    CreateAndLogDependencyException
    (EntitlementCodesOrchestrationService.Exeptions.cs:112-122), which is
    fed by the reference's dependency-shaped catches
    (Exeptions.cs:53-76).

    Two deliberate, cited divergences from the reference's tier set:

    1. No DependencyValidation tier. The reference pairs its Dependency tier
       with a DependencyValidation one
       (EntitlementCodeOrchestrationDependencyValidationException.cs, fed by
       CreateAndLogDependencyValidationException,
       Exeptions.cs:29-52 / :100-110). That tier exists to carry a *rejected
       input* bubbled up from the service beneath it. The Foundation services
       beneath Ingestion raise their *Validation* wrappers for that case, and
       Ingestion deliberately does not catch them: it validates topic and
       source_url itself before either call, so one arriving is a programming
       error routed to the catch-all service tier. Same reasoning the Review
       rebuild recorded in
       api/models/orchestrations/review/exceptions/review_orchestration_dependency_exception.py.

    2. The reference unwraps one level when building this
       (`innerException: exception.InnerException as Xeption`,
       Exeptions.cs:117). What Ingestion catches is likewise already a wrapper
       thrown by the layer beneath, but it is carried through whole rather
       than unwrapped, leaving the leaf reachable as
       `.inner_exception.inner_exception` -- identical to the Review rebuild's
       divergence note.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__("Ingestion dependency error occurred. Contact support.", inner_exception)
