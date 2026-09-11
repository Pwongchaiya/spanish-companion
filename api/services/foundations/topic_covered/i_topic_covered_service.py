"""Interface for the topic-covered Foundation service.

typing.Protocol, not abc.ABC, per this project's broker-interface waiver
(CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers table), extended to
service interfaces for the same reason as ILearnerProfileService.

Pure CRUD only -- 1:1 with ITopicCoveredBroker's actual surface
(select_by_profile/insert/touch). No find-by-topic, no upsert.
record_topic() (find-or-insert-or-touch) is Processing-tier logic, built
later against this interface (see
Projects/spanish-companion/entities/topic-covered.md).
"""

from typing import Protocol

from api.models.foundations.topic_covered.topic_covered import TopicCovered


class ITopicCoveredService(Protocol):
    """External-facing contract for TopicCovered's Foundation service."""

    def list_by_profile(self, profile_id: int) -> list[TopicCovered]:
        """All topics covered by the given profile.

        Raises TopicCoveredDependencyException (wrapping
        TopicCoveredUnavailableError) if the underlying broker call fails.
        Raises TopicCoveredServiceException for any other unexpected
        failure.
        """
        ...

    def create(self, profile_id: int, topic: str) -> TopicCovered:
        """Insert a new topic_covered row.

        Caller (Processing) is responsible for only calling this when the
        (profile_id, topic) pair doesn't already exist.

        Raises TopicCoveredValidationException (wrapping
        InvalidTopicCoveredInputError) if topic is None or blank.
        Raises TopicCoveredDependencyException (wrapping
        TopicCoveredUnavailableError) if the underlying broker call fails
        (including the unique constraint on (profile_id, topic)).
        Raises TopicCoveredServiceException for any other unexpected
        failure.
        """
        ...

    def touch(self, topic_id: int) -> TopicCovered:
        """Bump last_practiced_at to now for the given row.

        Raises TopicCoveredDependencyException (wrapping
        TopicCoveredUnavailableError) if the underlying broker call fails
        (including topic_id not existing).
        Raises TopicCoveredServiceException for any other unexpected
        failure.
        """
        ...
