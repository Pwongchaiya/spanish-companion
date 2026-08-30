"""Inner-tier exception for a genuinely unexpected failure."""

from api.errors import ApiError


class FailedReviewOrchestrationServiceException(ApiError):
    """Wraps a raw, unrecognised Exception before it is handed to
    CreateAndLogServiceException.

    Mirrors NL.Core.Entitlements.Api/Models/Orchestrations/EntitlementCodes/
    FailedEntitlementCodeOrchestrationServiceException.cs:12-14 -- note its
    constructor takes a plain `Exception` innerException, not a `Xeption`,
    because what it wraps is by definition outside the known vocabulary.

    This is the tier Session Lifecycle collapsed away (see
    api/models/session_lifecycle/exceptions/session_service_exception.py's
    "collapses that into one tier" note). Review keeps it: its fuller
    3-wrapper-tier shape is already closer to the reference, so the
    intermediate Failed* exception carries its weight here -- the raw
    Exception stays reachable as
    `service_exception.inner_exception.inner_exception` rather than being
    flattened one level up.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Failed review service error occurred. Contact support.",
            inner_exception=inner_exception,
        )
