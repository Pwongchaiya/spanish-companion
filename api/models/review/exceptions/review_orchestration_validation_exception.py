"""Exposure-tier exception wrapping a validation-tier leaf exception."""

from api.errors import ApiError


class ReviewOrchestrationValidationException(ApiError):
    """Wraps a leaf validation-tier exception (InvalidReviewOrchestrationException
    or NotFoundFlagException) for consumers, without leaking internals.

    Mirrors NL.Core.Entitlements.Api/Models/Orchestrations/EntitlementCodes/
    EntitlementCodeOrchestrationValidationException.cs:11-13 -- message +
    innerException, produced by CreateAndLogValidationException
    (EntitlementCodesOrchestrationService.Exeptions.cs:88-98).

    Both leaves land here, so the controller distinguishes them with an
    `isinstance(e.inner_exception, NotFoundFlagException)` check -- the
    Python translation of C#'s `catch (X) when (cond)` exception filter,
    same as api/controllers/session_lifecycle.py.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Review validation error occurred. Fix the errors and try again.",
            inner_exception=inner_exception,
        )
