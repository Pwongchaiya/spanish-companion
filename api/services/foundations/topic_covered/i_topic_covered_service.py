"""Interface for the topic-covered Foundation service.

typing.Protocol, not abc.ABC, per this project's broker-interface waiver
(CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers table), extended to
service interfaces for the same reason as IMistakePatternService.

Pure CRUD only — no upsert, no find-by-topic. record_topic()
(find-or-insert-or-touch) is Processing-tier logic, built against this
interface in topic_covered_processing_service.py.
"""

from typing import Protocol

from api.models.foundations.topic_covered.topic_covered import TopicCovered


class ITopicCoveredService(Protocol):
    """External-facing contract for TopicCovered's Foundation service.

    Method names embed the entity name, matching NL.Core.Users' Service
    interface methods (`AddUserProfileAsync`, `ModifyUserProfileAsync`,
    `RetrieveUserProfileByIdAsync` — IUserProfileService.cs) via the
    IMistakePatternService precedent — verbs stay this project's own
    list/create/touch, but the entity name is no longer dropped.
    """

    def list_topic_covered_by_profile(self, profile_id: int) -> list[TopicCovered]:
        """All topic_covered rows for the given profile.

        Raises TopicCoveredValidationException (wrapping
        InvalidTopicCoveredException) if profile_id is not a positive int.
        Raises TopicCoveredDependencyException (wrapping
        FailedTopicCoveredStorageException) if the underlying broker call
        fails.
        Raises TopicCoveredServiceException for any other unexpected
        failure.
        """
        ...

    def create_topic_covered(self, profile_id: int, topic: str) -> TopicCovered:
        """Insert a new topic_covered row.

        Caller (Processing) is responsible for only calling this when the
        (profile_id, topic) pair doesn't already exist.

        Raises TopicCoveredValidationException (wrapping
        InvalidTopicCoveredException) if profile_id is not a positive int
        or topic is None/blank.
        Raises TopicCoveredDependencyValidationException (wrapping
        AlreadyExistsTopicCoveredException) if (profile_id, topic) already
        exists (the unique constraint fires).
        Raises TopicCoveredDependencyException (wrapping
        FailedTopicCoveredStorageException) if the underlying broker call
        fails for any other reason.
        Raises TopicCoveredServiceException for any other unexpected
        failure.
        """
        ...

    def touch_topic_covered(self, topic_id: int) -> TopicCovered:
        """Bump last_practiced_at to now for the given row.

        Raises TopicCoveredValidationException (wrapping
        InvalidTopicCoveredException) if topic_id is not a positive int, or
        (wrapping NotFoundTopicCoveredException) if topic_id doesn't exist.
        Raises TopicCoveredDependencyException (wrapping
        FailedTopicCoveredStorageException) if the underlying broker call
        fails.
        Raises TopicCoveredServiceException for any other unexpected
        failure.
        """
        ...
