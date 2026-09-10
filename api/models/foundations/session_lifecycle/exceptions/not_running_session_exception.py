"""Leaf exception raised by ConversationSessionService.stop()."""

from api.errors import ApiError


class NotRunningSessionException(ApiError):
    """Raised by stop() when there is no active session to stop.

    Deliberately fail-fast rather than a silent no-op: symmetric with
    start()'s AlreadyRunningSessionException, and a stop() call against a
    session the caller believes is running but isn't signals a client-side
    state mismatch worth surfacing immediately rather than swallowing. Leaf
    exception -- always caught and wrapped into SessionValidationException,
    mirroring EntitlementService.Exeptions.cs:55-58 (NotFoundEntitlementException
    -> CreateAndLogValidationException).
    """

    def __init__(self) -> None:
        super().__init__("No conversation session is running")
