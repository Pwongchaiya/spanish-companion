"""Leaf dependency exception raised when a SessionLogBroker transcript call fails."""

from api.errors import ApiError


class LiveTranscriptUnavailableError(ApiError):
    """Raised when SessionLogBroker.clear_transcript() /
    append_transcript_line() fails.

    Name and shape mirror `FlagUnavailableError`
    (api/models/foundations/flag/exceptions/flag_unavailable_error.py) -- both name
    "the broker behind this is down". No `__init__` override: the inherited
    ApiError(message, inner_exception=None) constructor is message-only
    already.

    Leaf exception -- always caught and wrapped into
    LiveTranscriptDependencyException before leaving LiveTranscriptService.
    """
