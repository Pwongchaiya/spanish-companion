"""Leaf exception raised when a (profile_id, topic) row already exists.

A race, not a broken system: Processing's find-by-topic check
(list_topic_covered_by_profile then filter) and
TopicCoveredService.create_topic_covered() aren't atomic, so two concurrent
record_topic() calls for the same topic can both pass the find-by-topic
check and both call create_topic_covered(). The DB's unique constraint
(uq_topic_covered_profile_topic) is the backstop — this is the leaf raised
when it fires.

Mirrors NL.Core.Users' DuplicateKeyException -> AlreadyExistsUserProfileException
pairing (UserProfileService.Exceptions.cs:46-53), same shape as
AlreadyExistsMistakePatternException: a business-rule conflict detected via
the DB, not an input-shape problem, so it's wrapped into
TopicCoveredDependencyValidationException (not TopicCoveredValidationException)
before leaving the service.
"""

from api.errors import ApiError


class AlreadyExistsTopicCoveredException(ApiError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
