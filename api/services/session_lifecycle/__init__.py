from api.services.session_lifecycle.i_session_lifecycle_service import SessionLifecycleService
from api.services.session_lifecycle.session_lifecycle_service import (
    _ConversationSessionServiceBase,
    GRACEFUL_TIMEOUT_SECONDS,
    TERMINATE_TIMEOUT_SECONDS,
    READY_WARMUP_SECONDS,
)
from api.services.session_lifecycle.session_lifecycle_service_validations import (
    ConversationSessionServiceValidations,
)
from api.services.session_lifecycle.session_lifecycle_service_exceptions import (
    ConversationSessionServiceExceptions,
)


class ConversationSessionService(
    _ConversationSessionServiceBase,
    ConversationSessionServiceValidations,
    ConversationSessionServiceExceptions,
):
    """Combines the base logic, validations, and exceptions mixins into the
    concrete Foundation service -- mirrors C#'s `partial class` merging
    EntitlementService.cs / .Validations.cs / .Exeptions.cs into one class.
    """


__all__ = [
    "SessionLifecycleService",
    "ConversationSessionService",
    "GRACEFUL_TIMEOUT_SECONDS",
    "TERMINATE_TIMEOUT_SECONDS",
    "READY_WARMUP_SECONDS",
]
