"""Leaf validation exception raised when no session_audio row matches a lookup."""

from api.errors import ApiError


class NotFoundSessionAudioException(ApiError):
    def __init__(self) -> None:
        super().__init__("No session audio row exists for that lookup")
