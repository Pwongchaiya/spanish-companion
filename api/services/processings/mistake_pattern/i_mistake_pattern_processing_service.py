"""Interface for the mistake-pattern Processing service.

typing.Protocol, not abc.ABC -- same convention as the Foundation interface
(i_mistake_pattern_service.py) and this project's broker-interface waiver
(CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers), extended to service
interfaces project-wide.
"""

from datetime import datetime
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
        If the existing row is retired (status "resolved" and
        interval_days >= 30.0) the update also passes interval_days=1.0 and
        next_due_at=clock(): the pattern resurfaces, due immediately. Other
        rows' interval is untouched. Any exception from Foundation
        propagates unchanged.
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

    def record_review(self, profile_id: int, category: str, grade: str) -> MistakePattern:
        """Advance the (profile_id, category) row's review schedule (A1).

        interval_days: "again" -> 1.0 (reset); "hard" -> x1.2; "good" -> x2.0;
        "easy" -> x3.5. next_due_at = clock() + interval_days. Grade outside
        those four raises InvalidMistakePatternException; a pattern that was
        never recorded raises NotFoundMistakePatternException (same as
        resolve()). Foundation exceptions propagate unchanged.
        """
        ...

    def list_due(self, profile_id: int, now: datetime) -> list[MistakePattern]:
        """Rows for the profile with next_due_at not None and <= now,
        ordered by next_due_at ascending. Retired rows (status "resolved"
        and interval_days >= 30.0) are excluded. Foundation exceptions
        propagate unchanged.
        """
        ...
