"""Broker interface for `topic_covered` persistence.

`typing.Protocol`, not `ABC` — per CLAUDE.md's Broker-interfaces waiver
(matches `NL.Core.Entitlements`'s pattern of interfaces co-located with
their implementation). Pure CRUD only — no find-by-topic, no upsert.
`record_topic()` (find-or-insert-or-touch) is Processing-tier logic, built
against this interface in topic_covered_processing_service.py.
"""

from typing import Optional, Protocol

from api.models.foundations.topic_covered.topic_covered import TopicCovered


class ITopicCoveredBroker(Protocol):
    """External-resource boundary for `topic_covered` persistence. Raw
    SQLAlchemy CRUD only — no business logic, no exception handling.

    Method names embed the entity name (`insert_topic_covered`, not
    `insert`), matching NL.Core.Users' actual storage broker interface
    verbatim (`InsertUserProfileAsync`, `SelectUserProfileByIdAsync`,
    `UpdateUserProfileAsync` — IStorageBroker.UserProfiles.cs:14-17).
    """

    def select_topic_covered_by_profile(self, profile_id: int) -> list[TopicCovered]:
        """All topic_covered rows for the given profile."""
        ...

    def insert_topic_covered(self, profile_id: int, topic: str) -> TopicCovered:
        """Insert a new topic_covered row. Caller (Processing) is
        responsible for only ever calling this when no row exists yet for
        (profile_id, topic) — the DB unique constraint is the backstop.
        Lets sqlalchemy.exc.IntegrityError propagate unmodified if it does."""
        ...

    def touch_topic_covered(self, topic_id: int) -> Optional[TopicCovered]:
        """Bump last_practiced_at to now for the given row. Returns None if
        topic_id doesn't exist — Foundation maps that to
        NotFoundTopicCoveredException, same convention as
        IMistakePatternBroker.update_mistake_pattern()'s None-on-missing-id
        return (mistake_pattern_broker.py:57-68), which itself matches
        NL.Core.Users' SelectUserProfileByIdAsync->null->
        NotFoundUserProfileException path (UserProfileService.cs:42-53)."""
        ...
