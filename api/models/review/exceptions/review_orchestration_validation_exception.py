"""Exposure-tier exception wrapping a validation-tier leaf exception."""

from api.errors import ApiError


class ReviewOrchestrationValidationException(ApiError):
    """Wraps a Foundation-tier validation exception for consumers, without
    leaking internals.

    What lands here is FlagValidationException (holding NotFoundFlagException)
    or PracticeLogValidationException (holding
    InvalidPracticeAttemptException) -- the wrapper the Foundation service
    beneath raises, carried through whole rather than unwrapped. The leaf is
    therefore two levels deep, at `.inner_exception.inner_exception`.

    Mirrors NL.Core.Entitlements.Api/Models/Orchestrations/EntitlementCodes/
    EntitlementCodeOrchestrationValidationException.cs:11-13 -- message +
    innerException, produced by CreateAndLogValidationException
    (EntitlementCodesOrchestrationService.Exeptions.cs:88-98).

    Both wrappers land here, so the controller distinguishes them with an
    isinstance check on the nested leaf -- the Python translation of C#'s
    `catch (X) when (cond)` exception filter, same as
    api/controllers/session_lifecycle.py. api/controllers/review.py still
    checks only one level deep; correcting it belongs to the Exposer wave.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Review validation error occurred. Fix the errors and try again.",
            inner_exception=inner_exception,
        )
