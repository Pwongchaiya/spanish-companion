"""Leaf raised when the requested session has no session_log row."""

from api.errors import ApiError


class NotFoundSessionReplayException(ApiError):
    def __init__(self) -> None:
        super().__init__("No session log entry exists for that session id")
