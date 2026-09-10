"""Exposure-tier catch-all exception for ReviewOrchestrationService."""

from api.errors import ApiError


class ReviewOrchestrationServiceException(ApiError):
    """Catch-all wrapper for any exception not otherwise recognised --
    the final safety net so nothing escapes this service unwrapped.

    Mirrors NL.Core.Entitlements.Api/Models/Orchestrations/EntitlementCodes/
    EntitlementCodeOrchestrationServiceException.cs:11-13, produced by
    CreateAndLogServiceException
    (EntitlementCodesOrchestrationService.Exeptions.cs:124-134), which is
    fed the FailedEntitlementCodeOrchestrationServiceException built in the
    final `catch (Exception exception)` block (Exeptions.cs:77-85).

    So `inner_exception` here is always a
    FailedReviewOrchestrationServiceException, and the raw cause is one
    level further in.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Review service error occurred. Contact support.",
            inner_exception=inner_exception,
        )
