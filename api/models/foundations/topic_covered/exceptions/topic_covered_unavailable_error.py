"""Leaf dependency exception raised when an ITopicCoveredBroker call fails."""

from api.errors import ApiError


class TopicCoveredUnavailableError(ApiError):
    """Raised when select_by_profile()/insert()/touch() raises -- including
    touch() against a topic_id that doesn't exist, per
    ITopicCoveredBroker.touch()'s docstring ("raises whatever SQLAlchemy
    raises"). The broker doesn't distinguish missing-row from any other
    failure, so that case lands here rather than as a not-found leaf.

    Name and shape mirror LearnerProfileUnavailableError.

    Leaf exception -- always caught and wrapped into
    TopicCoveredDependencyException before leaving TopicCoveredService.
    """
