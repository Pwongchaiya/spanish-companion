"""Leaf dependency exception raised when an ITopicCoveredBroker call fails."""

from api.errors import ApiError


class FailedTopicCoveredStorageException(ApiError):
    """Raised when select_topic_covered_by_profile()/insert_topic_covered()/
    touch_topic_covered() raises anything other than a uniquely-classified
    IntegrityError (unique-constraint violations become
    AlreadyExistsTopicCoveredException instead).

    Named to match FailedUserProfileStorageException
    (UserProfileService.Exceptions.cs:39-44, 68-76) via the
    FailedMistakePatternStorageException precedent — this project's broker
    has no equivalent SqlException/DbUpdateException split (SQLAlchemyError
    covers both), so one leaf name covers what two leaf types cover in the
    reference.

    Leaf exception — always caught and wrapped into
    TopicCoveredDependencyException before leaving TopicCoveredService.
    """
