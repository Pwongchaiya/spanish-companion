"""Exposure-tier catch-all exception for IngestionService."""

from rag.errors import RagError


class IngestionOrchestrationServiceException(RagError):
    """Catch-all wrapper for any exception not otherwise recognised --
    the final safety net so nothing escapes this service unwrapped.

    Mirrors NL.Core.Entitlements.Api/Models/Orchestrations/EntitlementCodes/
    EntitlementCodeOrchestrationServiceException.cs:11-13, produced by
    CreateAndLogServiceException
    (EntitlementCodesOrchestrationService.Exeptions.cs:124-134) from the
    final `catch (Exception exception)` block (Exeptions.cs:77-85).

    Cited divergence -- the Failed* tier is collapsed away. The reference is
    two-step: the final catch builds a
    FailedEntitlementCodeOrchestrationServiceException
    (FailedEntitlementCodeOrchestrationServiceException.cs:12-14, built at
    Exeptions.cs:79-82) and hands *that* to CreateAndLogServiceException,
    so the raw cause sits two levels in. Here `inner_exception` is the raw
    Exception itself, one level in.

    This follows the Session Lifecycle precedent
    (api/models/session_lifecycle/exceptions/session_service_exception.py:10-17,
    "This project collapses that into one tier") rather than the Review one
    (api/models/review/exceptions/failed_review_orchestration_service_exception.py,
    which keeps the intermediate tier). Reason: Review keeps Failed* because
    it catches wrappers thrown by services beneath it, so the extra level
    distinguishes "a dependency's wrapper" from "a raw bug". Ingestion sits
    directly on brokers -- every genuinely unexpected exception reaching the
    final catch is already raw, so a Failed* tier would only wrap a raw
    exception in a second name that carries no extra information.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__("Ingestion service error occurred. Contact support.", inner_exception)
