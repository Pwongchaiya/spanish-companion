"""Leaf validation exception raised when an id doesn't exist in storage."""

from api.errors import ApiError


class NotFoundSessionLogEntryException(ApiError):
    """Raised by complete_session_log_entry() when the broker returns None
    for the given entry_id -- the row was never inserted, or was deleted
    between insert and completion.

    Mirrors NL.Core.Users' SelectUserProfileByIdAsync -> null ->
    NotFoundUserProfileException path (UserProfileService.cs:42-53) via
    NotFoundTopicCoveredException's precedent here.

    Leaf exception -- always caught and wrapped into
    SessionLogEntryValidationException before leaving
    SessionLogEntryService.
    """

    def __init__(self) -> None:
        super().__init__("No session_log row exists for that lookup")
