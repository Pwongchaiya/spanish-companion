"""Exposure-tier exception wrapping a failed dependency call."""

from rag.errors import RagError


class IngestionOrchestrationDependencyException(RagError):
    """Wraps IngestionUnavailableError -- a broker Ingestion depends on failed.

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
       input* bubbled up from a Processing service beneath it. Ingestion has
       no Processing layer beneath it -- it calls brokers directly per
       CLAUDE.md's ORC-002 waiver -- and a broker failure is an
       infrastructure outage, never a rejected input. Same reasoning the
       Review rebuild recorded in
       api/models/review/exceptions/review_orchestration_dependency_exception.py.

    2. The reference unwraps one level when building this
       (`innerException: exception.InnerException as Xeption`,
       Exeptions.cs:117) because what it catches is already a wrapper thrown
       by the Processing service beneath it. IngestionUnavailableError IS
       the leaf, so it is carried through whole rather than unwrapped into
       None -- identical to the Review rebuild's divergence note.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__("Ingestion dependency error occurred. Contact support.", inner_exception)
