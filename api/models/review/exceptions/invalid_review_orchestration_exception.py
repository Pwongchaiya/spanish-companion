"""Leaf validation exception raised by ReviewOrchestrator.record_practice()."""

from api.errors import ApiError


class InvalidReviewOrchestrationException(ApiError):
    """Raised by _validate_practice_input() when attempt_text is blank.

    Mirrors NL.Core.Entitlements.Api/Models/Orchestrations/EntitlementCodes/
    InvalidEntitlementCodeOrchestrationException.cs:11-13 -- message-only
    constructor, no innerException, raised from a named validation method
    (EntitlementCodesOrchestrationService.Validations.cs:12-17).

    ponytail: fixed message, no-arg constructor -- same shape as
    AlreadyRunningSessionException. The reference's `UpsertDataList` /
    `ThrowIfContainsErrors` multi-field mechanism
    (EntitlementCodesOrchestrationService.Validations.cs:32-50) exists to
    accumulate several field errors into one exception; Review has exactly
    one validated field, so the accumulator has nothing to accumulate.

    Message text is Phase 1's exact user-facing 400 body -- the controller
    renders `str(e.inner_exception)`, so moving this check from the
    controller into the service keeps the response body byte-identical.
    """

    def __init__(self) -> None:
        super().__init__("attempt_text is required")
