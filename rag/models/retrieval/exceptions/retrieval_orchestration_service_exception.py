"""Exposure-tier catch-all exception for HybridRetrievalService."""

from rag.errors import RagError


class RetrievalOrchestrationServiceException(RagError):
    """Catch-all wrapper for any exception not otherwise recognised --
    the final safety net so nothing escapes this service unwrapped.

    Mirrors NL.Core.Entitlements.Api/Models/Orchestrations/EntitlementCodes/
    EntitlementCodeOrchestrationServiceException.cs:11-13, produced by
    CreateAndLogServiceException
    (EntitlementCodesOrchestrationService.Exeptions.cs:124-134) from the
    final `catch (Exception exception)` block (Exeptions.cs:77-85).

    Cited divergence: the reference feeds that block through an
    intermediate FailedEntitlementCodeOrchestrationServiceException
    (Exeptions.cs:79-82, FailedEntitlementCodeOrchestrationServiceException.cs:12-14).
    Retrieval collapses that into one tier -- `inner_exception` is the raw
    cause directly -- following
    api/models/session_lifecycle/exceptions/session_service_exception.py:10-17's
    already-established collapse in this codebase rather than Review's
    fuller 3-wrapper-tier shape. Retrieval has exactly one recognised
    failure category (RetrievalUnavailableError), so there is nothing for
    the extra level of indirection to disambiguate.

    Note what this tier does NOT catch: `retrieve()`'s bare ValueError for a
    blank query or top_k < 1 is raised *outside* _try_catch and propagates
    completely raw. Review only ever passes a validated flag.corrected and
    the module-level RETRIEVAL_TOP_K, so a ValueError from there is a
    programming error, not an expected condition -- which is also why
    Retrieval has no Validation tier and no retrieval_service_validations.py
    sibling to Exeptions.cs's .Validations.cs.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__("Retrieval service error occurred. Contact support.", inner_exception)
