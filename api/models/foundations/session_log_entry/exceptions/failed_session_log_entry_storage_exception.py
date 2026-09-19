"""Leaf dependency exception raised when an ISessionLogEntryBroker call fails."""

from api.errors import ApiError


class FailedSessionLogEntryStorageException(ApiError):
    """Raised when insert_session_log_entry()/select_all_session_log_entries()/
    update_session_log_entry() raises any SQLAlchemyError.

    Unlike TopicCovered/MistakePattern there is no unique constraint on
    `session_log`, so there is no AlreadyExists*/DependencyValidation tier
    here -- every IntegrityError is as much a storage failure as a
    connection drop, and gets this one leaf.

    Named to match FailedUserProfileStorageException
    (UserProfileService.Exceptions.cs:39-44, 68-76) via the
    FailedTopicCoveredStorageException precedent.

    Leaf exception -- always caught and wrapped into
    SessionLogEntryDependencyException before leaving
    SessionLogEntryService.
    """
