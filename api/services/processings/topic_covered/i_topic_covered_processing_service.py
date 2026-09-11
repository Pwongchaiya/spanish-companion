"""Interface for the topic-covered Processing service.

typing.Protocol, not abc.ABC -- same convention as the Foundation interface
(i_topic_covered_service.py) and this project's broker-interface waiver
(CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers), extended to service
interfaces project-wide.
"""

from typing import Protocol

from api.models.foundations.topic_covered.topic_covered import TopicCovered


class ITopicCoveredProcessingService(Protocol):
    """External-facing contract for TopicCovered's Processing service."""

    def record_topic(self, profile_id: int, topic: str) -> TopicCovered:
        """Find-or-touch-or-create for a (profile_id, topic) pair.

        Calls Foundation's list_by_profile(profile_id) and looks for a row
        matching topic. If found, calls touch(topic_id) to bump
        last_practiced_at. If not found, calls create(profile_id, topic),
        which sets first_covered_at. Any exception from Foundation
        propagates unchanged.
        """
        ...
