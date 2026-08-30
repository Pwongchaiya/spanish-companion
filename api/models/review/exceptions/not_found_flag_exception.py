"""Leaf validation exception raised when a flag id matches nothing."""

from api.errors import ApiError


class NotFoundFlagException(ApiError):
    """Raised by _get_flag() when no flag in the current list has this id.

    Named `<Condition><Entity>` after NL.Core.Entitlements.Api/Models/
    Foundations/Entitlements/Exceptions/NotFoundEntitlementException.cs,
    matching the AlreadyRunningSessionException / NotRunningSessionException
    convention already established by the Session Lifecycle rebuild.
    (Was `FlagNotFoundException` before this rebuild.)

    Leaf exception -- always caught and wrapped into
    ReviewOrchestrationValidationException before leaving this service,
    mirroring EntitlementCodesOrchestrationService.Exeptions.cs:25-28.
    """

    def __init__(self, flag_id: str) -> None:
        super().__init__(f"No flag found with id {flag_id!r}")
