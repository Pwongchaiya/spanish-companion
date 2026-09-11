"""Foundation service for the mistake_pattern entity.

Wraps IMistakePatternBroker (api/brokers/mistake_pattern/) with input
validation only -- pure CRUD, no upsert, no find-by-category.
record_occurrence()/resolve() (find-by-category over list_by_profile's
results, then insert-or-increment) are Processing-tier logic per CLAUDE.md's
Processing-row reversal and the entity doc
(Projects/spanish-companion/entities/mistake-pattern.md).

Single broker dependency -> Foundation layer, not Orchestration, per
CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers.

Split into a base logic file plus Validations/Exceptions mixins (this file,
mistake_pattern_service_validations.py, mistake_pattern_service_exceptions.py),
combined into the concrete MistakePatternService in __init__.py -- mirrors
C#'s `partial class` merging multiple files into one class
(python-adaptations-skill.md's Architecture Patterns table), the same
pattern used for LearnerProfile in this codebase.
"""

from api.brokers.logging import LoggingBroker
from api.brokers.mistake_pattern.i_mistake_pattern_broker import IMistakePatternBroker
from api.models.foundations.mistake_pattern.exceptions import MistakePatternUnavailableError
from api.models.foundations.mistake_pattern.mistake_pattern import MistakePattern


class _MistakePatternServiceBase:
    """Owns MistakePattern CRUD.

    Public methods delegate to a private `_do_thing` method through
    `_try_catch` (defined in the Exceptions mixin), per python-adaptations-
    skill.md's TryCatch translation. Validation checks are named methods
    (defined in the Validations mixin) rather than inlined.
    """

    def __init__(
        self,
        broker: IMistakePatternBroker,
        *,
        logging_broker: LoggingBroker,
    ) -> None:
        self._broker = broker
        self._logging_broker = logging_broker

    def list_by_profile(self, profile_id: int) -> list[MistakePattern]:
        return self._try_catch(lambda: self._list_by_profile(profile_id))

    def _list_by_profile(self, profile_id: int) -> list[MistakePattern]:
        self._validate_profile_id(profile_id)
        try:
            return self._broker.select_by_profile(profile_id)
        except Exception as e:
            raise MistakePatternUnavailableError(str(e)) from e

    def create(self, profile_id: int, category: str) -> MistakePattern:
        return self._try_catch(lambda: self._create(profile_id, category))

    def _create(self, profile_id: int, category: str) -> MistakePattern:
        self._validate_profile_id(profile_id)
        self._validate_category(category)
        try:
            return self._broker.insert(profile_id, category)
        except Exception as e:
            raise MistakePatternUnavailableError(str(e)) from e

    def update(self, pattern_id: int, occurrence_count: int, status: str) -> MistakePattern:
        return self._try_catch(lambda: self._update(pattern_id, occurrence_count, status))

    def _update(self, pattern_id: int, occurrence_count: int, status: str) -> MistakePattern:
        self._validate_pattern_id(pattern_id)
        self._validate_occurrence_count(occurrence_count)
        self._validate_status(status)
        try:
            return self._broker.update(pattern_id, occurrence_count, status)
        except Exception as e:
            raise MistakePatternUnavailableError(str(e)) from e


if __name__ == "__main__":
    # ponytail: self-check for the branches worth testing without a live
    # broker/DB -- validation rejects bad input before ever reaching the
    # broker, for all three public methods. Full behaviour (broker
    # success/failure paths) is normally covered by the Test Writer Agent's
    # suite, but this project's "no tests during build" waiver
    # (CLAUDE.md / MEMORY.md) defers that to a later pass, so this is the
    # one runnable check for now.
    from unittest.mock import Mock

    from api.models.foundations.mistake_pattern.exceptions import MistakePatternValidationException
    from api.services.foundations.mistake_pattern import MistakePatternService

    broker = Mock()
    service = MistakePatternService(broker, logging_broker=Mock())

    for bad_profile_id in (None, 0, -1):
        try:
            service.list_by_profile(bad_profile_id)
            raise AssertionError(f"expected rejection for profile_id={bad_profile_id!r}")
        except MistakePatternValidationException:
            pass
    assert broker.select_by_profile.call_count == 0, "broker must not be called on invalid profile_id"

    for bad_category in (None, "", "   "):
        try:
            service.create(1, bad_category)
            raise AssertionError(f"expected rejection for category={bad_category!r}")
        except MistakePatternValidationException:
            pass
    assert broker.insert.call_count == 0, "broker must not be called on invalid category"

    for bad_count, bad_status in ((0, "active"), (1, "done")):
        try:
            service.update(1, bad_count, bad_status)
            raise AssertionError(f"expected rejection for ({bad_count!r}, {bad_status!r})")
        except MistakePatternValidationException:
            pass
    assert broker.update.call_count == 0, "broker must not be called on invalid update input"

    broker.insert.return_value = MistakePattern(
        id=1, profile_id=1, category="ser vs estar", occurrence_count=1, last_seen_at=None, status="active"
    )
    created = service.create(1, "ser vs estar")
    assert created.category == "ser vs estar"
    broker.insert.assert_called_once_with(1, "ser vs estar")

    print("mistake_pattern_service self-check passed")
