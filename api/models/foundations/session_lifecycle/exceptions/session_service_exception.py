"""Exposure-tier catch-all exception for ConversationSessionService."""

from api.errors import ApiError


class SessionServiceException(ApiError):
    """Catch-all wrapper for any exception not otherwise recognised --
    the final safety net so nothing escapes this service unwrapped.

    Mirrors EntitlementService.Exeptions.cs:85-93's final
    `catch (Exception exception)` block, which every TryCatch method in the
    reference project ends with (EntitlementService.Exeptions.cs:85-93 and
    :111-119) -- wraps into FailedEntitlementServiceException ->
    EntitlementServiceException. This project collapses that into one tier
    (no separate Failed*ServiceException) since Session Lifecycle has no
    storage/dependency layer beneath it worth distinguishing yet -- see this
    dispatch's scope note on why no Dependency tier was added.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Session service error occurred. Contact support.",
            inner_exception=inner_exception,
        )
