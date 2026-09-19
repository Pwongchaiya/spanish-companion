"""Processing service for the mistake_pattern entity.

Higher-order logic on top of the single Foundation dependency
(IMistakePatternService): find-by-category (over
list_mistake_patterns_by_profile's results) composed with
insert-or-increment / resolve. Foundation stays pure CRUD (see
mistake_pattern_service.py's docstring) -- this is exactly the composition
the Processing tier exists for per CLAUDE.md's Processing-row reversal and
the entity doc (Projects/spanish-companion/entities/mistake-pattern.md).

Two methods, both do-or-delegate: each decides which Foundation call(s) to
make from the find-by-category result, then delegates entirely -- neither
transforms a Foundation response afterward. No base/validations/exceptions
mixin split (that split earns its keep once there's per-method noise to
organise; see Foundation's three-file layout for when it does -- same call
made for LearnerProfileProcessingService).
"""

from datetime import datetime, timedelta
from typing import Callable

from api.models.foundations.mistake_pattern.exceptions import (
    InvalidMistakePatternException,
    NotFoundMistakePatternException,
)
from api.models.foundations.mistake_pattern.mistake_pattern import MistakePattern
from api.services.foundations.mistake_pattern.i_mistake_pattern_service import IMistakePatternService

# Grade -> interval multiplier. None = reset to 1.0 day ("again").
_INTERVAL_MULTIPLIERS: dict[str, float | None] = {"again": None, "hard": 1.2, "good": 2.0, "easy": 3.5}


class MistakePatternProcessingService:
    """Find-by-category over Foundation's list_mistake_patterns_by_profile(),
    then delegates to create_mistake_pattern/update_mistake_pattern.
    Foundation has no single-row read path (see i_mistake_pattern_service.py's
    docstring) so the find happens here, in Python, over the full
    per-profile list.
    """

    def __init__(
        self,
        mistake_pattern_service: IMistakePatternService,
        clock: Callable[[], datetime] = datetime.now,
    ) -> None:
        self._mistake_pattern_service = mistake_pattern_service
        self._clock = clock

    def record_review(self, profile_id: int, category: str, grade: str) -> MistakePattern:
        if grade not in _INTERVAL_MULTIPLIERS:
            exception = InvalidMistakePatternException()
            exception.upsert_data_list("grade", "Grade is not recognized")
            exception.throw_if_contains_errors()
        existing = self._find_by_category(profile_id, category)
        if existing is None:
            raise NotFoundMistakePatternException()
        multiplier = _INTERVAL_MULTIPLIERS[grade]
        interval_days = 1.0 if multiplier is None else existing.interval_days * multiplier
        return self._mistake_pattern_service.update_mistake_pattern(
            existing.id,
            occurrence_count=existing.occurrence_count,
            status=existing.status,
            interval_days=interval_days,
            next_due_at=self._clock() + timedelta(days=interval_days),
        )

    def list_due(self, profile_id: int, now: datetime) -> list[MistakePattern]:
        rows = self._mistake_pattern_service.list_mistake_patterns_by_profile(profile_id)
        due = [row for row in rows if row.next_due_at is not None and row.next_due_at <= now]
        return sorted(due, key=lambda row: row.next_due_at)

    def record_occurrence(self, profile_id: int, category: str) -> MistakePattern:
        existing = self._find_by_category(profile_id, category)
        if existing is None:
            return self._mistake_pattern_service.create_mistake_pattern(profile_id, category)
        return self._mistake_pattern_service.update_mistake_pattern(
            existing.id, occurrence_count=existing.occurrence_count + 1, status="active"
        )

    def resolve(self, profile_id: int, category: str) -> MistakePattern:
        existing = self._find_by_category(profile_id, category)
        if existing is None:
            raise NotFoundMistakePatternException()
        return self._mistake_pattern_service.update_mistake_pattern(
            existing.id, occurrence_count=existing.occurrence_count, status="resolved"
        )

    def _find_by_category(self, profile_id: int, category: str) -> MistakePattern | None:
        rows = self._mistake_pattern_service.list_mistake_patterns_by_profile(profile_id)
        return next((row for row in rows if row.category == category), None)
