from api.services.foundations.session_lifecycle.i_session_lifecycle_service import SessionLifecycleService
from api.services.foundations.session_lifecycle.session_lifecycle_service import _ConversationSessionServiceBase
from api.services.foundations.session_lifecycle.session_lifecycle_service_validations import (
    ConversationSessionServiceValidations,
)
from api.services.foundations.session_lifecycle.session_lifecycle_service_exceptions import (
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
]
