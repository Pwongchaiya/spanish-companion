"""Leaf exception raised by ConversationSessionService.start()."""

from api.errors import ApiError


class AlreadyRunningSessionException(ApiError):
    """Raised by start() when a session is already active.

    BotProcessBroker.start() has no such guard by design (see its
    docstring) -- this service owns the refusal. Leaf exception -- always
    caught and wrapped into SessionValidationException before leaving this
    service, mirroring NL.Core.Entitlements.Api/Services/Foundations/
    Entitlements/EntitlementService.Exeptions.cs:37-45 (DuplicateKeyException
    -> AlreadyExistsEntitlementException -> wrapped via
    CreateAndLogValidationException).
    """

    def __init__(self) -> None:
        super().__init__("A conversation session is already running")
