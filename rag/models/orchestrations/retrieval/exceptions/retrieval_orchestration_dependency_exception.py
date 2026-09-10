"""Exposure-tier exception wrapping a failed retrieval dependency call."""

from rag.errors import RagError


class RetrievalOrchestrationDependencyException(RagError):
    """Wraps a dependency failure raised inside Retrieval's pipeline.

    Mirrors NL.Core.Entitlements.Api/Models/Orchestrations/EntitlementCodes/
    EntitlementCodeOrchestrationDependencyException.cs:11-13, produced by
    CreateAndLogDependencyException
    (EntitlementCodesOrchestrationService.Exeptions.cs:112-122).

    It wraps exactly two things today, both Foundation-tier wrappers:
    `EmbeddingModelDependencyException` and
    `ChunkRepositoryDependencyException` -- the embedding model or chunk
    store being unreachable. (Before the Foundation tier existed beneath
    this service it wrapped a local `RetrievalUnavailableError` leaf, now
    deleted: the Foundation services raise their own wrapped equivalents.)

    This is the type api/services/review/ now catches. Retrieval sits
    directly beneath Review in the call graph (ReviewOrchestrationService ->
    RetrievalController.retrieve()), with no Processing layer between, so
    the cross-service shape matches Exeptions.cs:53-76 exactly: the outer
    service catches the *wrapper* types the service beneath it raises, not
    that service's raw leaves.

    Two deliberate, cited divergences from the reference's tier set:

    1. No DependencyValidation tier. The reference pairs every Dependency
       tier with a DependencyValidation one
       (EntitlementCodeOrchestrationDependencyValidationException.cs, fed by
       Exeptions.cs:29-52). Retrieval's dependency failure modes are both
       infrastructure outages rather than rejected inputs, so there is
       nothing validation-shaped for that tier to carry. Same reasoning
       already recorded for Review in
       api/models/orchestrations/review/exceptions/review_orchestration_dependency_exception.py.

    2. Cited divergence from Exeptions.cs:117
       (`innerException: exception.InnerException as Xeption`): the
       reference unwraps one level because what it catches is itself
       already a wrapper from the service beneath it. Retrieval now catches
       exactly that shape -- a Foundation-tier wrapper -- but still carries
       it through whole rather than flattening it, so the raw
       *UnavailableError leaf stays reachable as
       `.inner_exception.inner_exception`. Same call Review makes one tier
       up, which means from Review's side the leaf now sits three deep.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__("Retrieval dependency error occurred. Contact support.", inner_exception)
