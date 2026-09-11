"""Leaf dependency exception raised when an IMistakePatternBroker call fails."""

from api.errors import ApiError


class FailedMistakePatternStorageException(ApiError):
    """Raised when select_by_profile()/insert()/update() raises anything
    other than a uniquely-classified IntegrityError (unique-constraint
    violations become AlreadyExistsMistakePatternException instead).

    Named to match FailedUserProfileStorageException
    (UserProfileService.Exceptions.cs:39-44, 68-76) -- the reference's own
    generic storage-failure leaf, wrapped from both SqlException and
    DbUpdateException there. This project's broker has no equivalent
    SqlException/DbUpdateException split (SQLAlchemyError covers both), so
    one leaf name covers what two leaf types cover in the reference.

    Leaf exception -- always caught and wrapped into
    MistakePatternDependencyException before leaving MistakePatternService.
    """
