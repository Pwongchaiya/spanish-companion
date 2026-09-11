"""Interface for the mistake-pattern Processing service.

typing.Protocol, not abc.ABC -- same convention as the Foundation interface
(i_mistake_pattern_service.py) and this project's broker-interface waiver
(CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers), extended to service
interfaces project-wide.
"""

from typing import Protocol

from api.models.foundations.mistake_pattern.mistake_pattern import MistakePattern


class IMistakePatternProcessingService(Protocol):
    """External-facing contract for MistakePattern's Processing service."""

    def record_occurrence(self, profile_id: int, category: str) -> MistakePattern:
        """Find-or-create-and-increment for a (profile_id, category) row.

        Calls Foundation's list_by_profile(profile_id) and finds a row
        matching category in Python. If found, calls update() with
        occurrence_count + 1 and status="active" (reactivating a previously
        resolved pattern). If not found, calls create(profile_id, category).
        Any exception from Foundation propagates unchanged.
        """
        ...

    def resolve(self, profile_id: int, category: str) -> MistakePattern:
        """Mark a (profile_id, category) row as resolved.

        Calls Foundation's list_by_profile(profile_id) and finds a row
        matching category in Python. If found, calls update() with the same
        occurrence_count and status="resolved". If not found, raises
        NotFoundMistakePatternException -- a pattern that was never recorded
        can't be resolved. Any exception from Foundation propagates
        unchanged.
        """
        ...
