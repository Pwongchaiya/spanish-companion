from api.services.foundations.session_log.i_session_log_service import ISessionLogService
from api.services.foundations.session_log.session_log_service import _SessionLogServiceBase
from api.services.foundations.session_log.session_log_service_exceptions import (
    SessionLogServiceExceptions,
)


class SessionLogService(_SessionLogServiceBase, SessionLogServiceExceptions):
    """Combines the base logic and exceptions mixins into the concrete
    Foundation service -- mirrors FlagService's multi-inheritance merge,
    which stands in for C#'s `partial class`.
    """


__all__ = [
    "ISessionLogService",
    "SessionLogService",
]
