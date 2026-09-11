"""Leaf dependency exception raised when an ILearnerProfileBroker call fails."""

from api.errors import ApiError


class FailedLearnerProfileStorageException(ApiError):
    """Raised when select_learner_profile()/insert_learner_profile()/
    update_learner_profile() raises anything (e.g. a raw SQLAlchemyError --
    the broker does no wrapping of its own).

    Named to match FailedUserProfileStorageException
    (UserProfileService.Exceptions.cs:39-44, 68-76) -- same convention
    already applied to FailedMistakePatternStorageException. Names "the
    broker behind this is down", not a legitimate empty result
    (select_learner_profile() returning None is not this; that's
    NotFoundLearnerProfileException, a validation-tier condition).

    Leaf exception -- always caught and wrapped into
    LearnerProfileDependencyException before leaving LearnerProfileService.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
