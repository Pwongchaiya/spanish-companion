"""Broker interface for the `topic_covered` table.

`typing.Protocol`, not `ABC` — per CLAUDE.md's Broker-interfaces waiver
(matches `NL.Core.Entitlements`'s `IEntitlementService.cs` sitting next to
its implementation, not the toolkit's ABC default). Pure CRUD only — no
find-by-topic, no upsert. `record_topic()` (find-or-insert-or-touch) is
Processing-tier logic, built later against this interface.
"""

from typing import Protocol

from api.models.foundations.topic_covered.topic_covered import TopicCovered


class ITopicCoveredBroker(Protocol):
    """External-resource boundary for `topic_covered` persistence. Raw
    SQLAlchemy CRUD only — no business logic, no exception handling."""

    def select_by_profile(self, profile_id: int) -> list[TopicCovered]:
        """All topics covered by the given profile."""
        ...

    def insert(self, profile_id: int, topic: str) -> TopicCovered:
        """Insert a new topic_covered row. Caller (Processing) is
        responsible for only calling this when the (profile_id, topic) pair
        doesn't already exist — the unique constraint enforces it."""
        ...

    def touch(self, topic_id: int) -> TopicCovered:
        """Bump last_practiced_at to now for the given row. Raises whatever
        SQLAlchemy raises if topic_id doesn't exist — Foundation maps that
        per the exception-hierarchy skill."""
        ...
