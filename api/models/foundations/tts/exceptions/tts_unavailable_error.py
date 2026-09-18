"""Leaf dependency exception raised when a TtsBroker call fails."""

from api.errors import ApiError


class TtsUnavailableError(ApiError):
    """Raised when TtsBroker.synthesize() fails -- network error, bad Azure
    Speech credentials, or a non-completed synthesis result.

    Name and shape mirror FlagUnavailableError
    (api/models/foundations/flag/exceptions/flag_unavailable_error.py):
    "the broker behind this is down", not a legitimate empty result. No
    `__init__` override -- the inherited ApiError(message,
    inner_exception=None) constructor is message-only already.

    Leaf exception -- always caught and wrapped into TtsDependencyException
    before leaving TtsService.
    """
