"""Leaf dependency exception raised when a SessionLogBroker write fails."""

from api.errors import ApiError


class SessionLogUnavailableError(ApiError):
    """Raised when SessionLogBroker.write_session_log() fails.

    Name and shape mirror `FlagUnavailableError`
    (api/models/foundations/flag/exceptions/flag_unavailable_error.py) -- both name
    "the broker behind this is down". No `__init__` override: the inherited
    ApiError(message, inner_exception=None) constructor is message-only
    already.

    Leaf exception -- always caught and wrapped into
    SessionLogDependencyException before leaving SessionLogService.
    """
