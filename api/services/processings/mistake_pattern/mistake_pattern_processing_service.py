"""Processing service for the mistake_pattern entity.

Higher-order logic on top of the single Foundation dependency
(IMistakePatternService): find-by-category (over list_by_profile's results)
composed with insert-or-increment / resolve. Foundation stays pure CRUD (see
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

from api.models.foundations.mistake_pattern.exceptions import NotFoundMistakePatternException
from api.models.foundations.mistake_pattern.mistake_pattern import MistakePattern
from api.services.foundations.mistake_pattern.i_mistake_pattern_service import IMistakePatternService


class MistakePatternProcessingService:
    """Find-by-category over Foundation's list_by_profile(), then delegates
    to create/update. Foundation has no single-row read path (see
    i_mistake_pattern_service.py's docstring) so the find happens here, in
    Python, over the full per-profile list.
    """

    def __init__(self, mistake_pattern_service: IMistakePatternService) -> None:
        self._mistake_pattern_service = mistake_pattern_service

    def record_occurrence(self, profile_id: int, category: str) -> MistakePattern:
        existing = self._find_by_category(profile_id, category)
        if existing is None:
            return self._mistake_pattern_service.create(profile_id, category)
        return self._mistake_pattern_service.update(
            existing.id, occurrence_count=existing.occurrence_count + 1, status="active"
        )

    def resolve(self, profile_id: int, category: str) -> MistakePattern:
        existing = self._find_by_category(profile_id, category)
        if existing is None:
            raise NotFoundMistakePatternException()
        return self._mistake_pattern_service.update(
            existing.id, occurrence_count=existing.occurrence_count, status="resolved"
        )

    def _find_by_category(self, profile_id: int, category: str) -> MistakePattern | None:
        rows = self._mistake_pattern_service.list_by_profile(profile_id)
        return next((row for row in rows if row.category == category), None)


if __name__ == "__main__":
    # ponytail: the one runnable check -- both find-by-category branches for
    # each method, against a mocked Foundation service (per test-processing-
    # skill.md's "always mock Foundation" rule, done here as a lightweight
    # self-check since CLAUDE.md's "no tests during build" waiver applies).
    from datetime import datetime
    from unittest.mock import Mock

    existing = MistakePattern(
        id=1, profile_id=1, category="ser vs estar", occurrence_count=2, last_seen_at=datetime.now(), status="resolved"
    )

    # record_occurrence: found -> increment + reactivate
    foundation = Mock()
    foundation.list_by_profile.return_value = [existing]
    incremented = MistakePattern(
        id=1, profile_id=1, category="ser vs estar", occurrence_count=3, last_seen_at=datetime.now(), status="active"
    )
    foundation.update.return_value = incremented
    service = MistakePatternProcessingService(foundation)

    assert service.record_occurrence(1, "ser vs estar") is incremented
    foundation.update.assert_called_once_with(1, occurrence_count=3, status="active")
    foundation.create.assert_not_called()

    # record_occurrence: not found -> create
    foundation = Mock()
    foundation.list_by_profile.return_value = []
    created = MistakePattern(
        id=2, profile_id=1, category="gender agreement", occurrence_count=1, last_seen_at=datetime.now(), status="active"
    )
    foundation.create.return_value = created
    service = MistakePatternProcessingService(foundation)

    assert service.record_occurrence(1, "gender agreement") is created
    foundation.create.assert_called_once_with(1, "gender agreement")
    foundation.update.assert_not_called()

    # resolve: found -> update with status="resolved", same occurrence_count
    active = MistakePattern(
        id=3, profile_id=1, category="subjunctive", occurrence_count=4, last_seen_at=datetime.now(), status="active"
    )
    foundation = Mock()
    foundation.list_by_profile.return_value = [active]
    resolved = MistakePattern(
        id=3, profile_id=1, category="subjunctive", occurrence_count=4, last_seen_at=datetime.now(), status="resolved"
    )
    foundation.update.return_value = resolved
    service = MistakePatternProcessingService(foundation)

    assert service.resolve(1, "subjunctive") is resolved
    foundation.update.assert_called_once_with(3, occurrence_count=4, status="resolved")

    # resolve: not found -> raises
    foundation = Mock()
    foundation.list_by_profile.return_value = []
    service = MistakePatternProcessingService(foundation)

    try:
        service.resolve(1, "no such category")
        raise AssertionError("expected NotFoundMistakePatternException")
    except NotFoundMistakePatternException:
        pass
    foundation.update.assert_not_called()

    print("mistake_pattern_processing_service self-check passed")
