"""Exposure-tier exception wrapping a failed retrieval dependency call."""

from rag.errors import RagError


class RetrievalOrchestrationDependencyException(RagError):
    """Wraps a dependency failure raised inside Retrieval's pipeline.

    Mirrors NL.Core.Entitlements.Api/Models/Orchestrations/EntitlementCodes/
    EntitlementCodeOrchestrationDependencyException.cs:11-13, produced by
    CreateAndLogDependencyException
    (EntitlementCodesOrchestrationService.Exeptions.cs:112-122).

    It wraps exactly one thing today: `RetrievalUnavailableError` -- the
    chunk store or embedding model being unreachable.

    This is the type api/services/review/ now catches. Retrieval sits
    directly beneath Review in the call graph (ReviewOrchestrator ->
    RetrievalController.retrieve()), with no Processing layer between, so
    the cross-service shape matches Exeptions.cs:53-76 exactly: the outer
    service catches the *wrapper* types the service beneath it raises, not
    that service's raw leaves.

    Two deliberate, cited divergences from the reference's tier set:

    1. No DependencyValidation tier. The reference pairs every Dependency
       tier with a DependencyValidation one
       (EntitlementCodeOrchestrationDependencyValidationException.cs, fed by
       Exeptions.cs:29-52). Retrieval's only dependency failure mode,
       RetrievalUnavailableError, is an infrastructure outage rather than a
       rejected input, so there is nothing validation-shaped for that tier
       to carry. Same reasoning already recorded for Review in
       api/models/review/exceptions/review_orchestration_dependency_exception.py.

    2. Cited divergence from Exeptions.cs:117
       (`innerException: exception.InnerException as Xeption`): the
       reference unwraps one level because what it catches is itself
       already a wrapper from the Processing service beneath it. Retrieval
       catches RetrievalUnavailableError, which IS the leaf -- there is no
       layer beneath it here -- so it is carried through whole rather than
       unwrapped into None. (Review's pre-rebuild note said the same thing
       about this leaf; after this rebuild that reasoning lives here, one
       tier down, and Review's own catch is now a wrapper-of-wrapper.)
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__("Retrieval dependency error occurred. Contact support.", inner_exception)
