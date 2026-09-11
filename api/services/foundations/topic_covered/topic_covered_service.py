"""Foundation service for topic_covered.

Wraps ITopicCoveredBroker (api/brokers/topic_covered/) with input
validation only -- pure CRUD, 1:1 with the broker's actual surface
(select_by_profile/insert/touch). No upsert, no find-by-topic.
record_topic() (find-or-insert-or-touch) is Processing-tier logic per
CLAUDE.md's Processing-row reversal and the entity doc
(Projects/spanish-companion/entities/topic-covered.md).

Single broker dependency -> Foundation layer, not Orchestration, per
CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers.

Split into a base logic file plus Validations/Exceptions mixins (this file,
topic_covered_service_validations.py, topic_covered_service_exceptions.py),
combined into the concrete TopicCoveredService in __init__.py -- mirrors
C#'s `partial class` merging multiple files into one class
(python-adaptations-skill.md's Architecture Patterns table), the same
pattern used for LearnerProfile in this codebase.
"""

from api.brokers.logging import LoggingBroker
from api.brokers.topic_covered import ITopicCoveredBroker
from api.models.foundations.topic_covered.exceptions import TopicCoveredUnavailableError
from api.models.foundations.topic_covered.topic_covered import TopicCovered


class _TopicCoveredServiceBase:
    """Owns TopicCovered CRUD.

    Public methods delegate to a private `_do_thing` method through
    `_try_catch` (defined in the Exceptions mixin), per python-adaptations-
    skill.md's TryCatch translation. Validation checks are named methods
    (defined in the Validations mixin) rather than inlined.
    """

    def __init__(
        self,
        broker: ITopicCoveredBroker,
        *,
        logging_broker: LoggingBroker,
    ) -> None:
        self._broker = broker
        self._logging_broker = logging_broker

    def list_by_profile(self, profile_id: int) -> list[TopicCovered]:
        return self._try_catch(lambda: self._list_by_profile(profile_id))

    def _list_by_profile(self, profile_id: int) -> list[TopicCovered]:
        try:
            return self._broker.select_by_profile(profile_id)
        except Exception as e:
            raise TopicCoveredUnavailableError(str(e)) from e

    def create(self, profile_id: int, topic: str) -> TopicCovered:
        return self._try_catch(lambda: self._create(profile_id, topic))

    def _create(self, profile_id: int, topic: str) -> TopicCovered:
        self._validate_topic(topic)
        try:
            return self._broker.insert(profile_id, topic)
        except Exception as e:
            raise TopicCoveredUnavailableError(str(e)) from e

    def touch(self, topic_id: int) -> TopicCovered:
        return self._try_catch(lambda: self._touch(topic_id))

    def _touch(self, topic_id: int) -> TopicCovered:
        try:
            return self._broker.touch(topic_id)
        except Exception as e:
            raise TopicCoveredUnavailableError(str(e)) from e


if __name__ == "__main__":
    # ponytail: self-check for the one branch worth testing without a live
    # broker/DB -- validation rejects blank/None topic before ever reaching
    # the broker, and a valid call passes straight through. Full behaviour
    # (broker success/failure paths) is covered by the Test Writer Agent's
    # suite; this project's Phase 2 test strategy has no separate
    # assert-based check requirement once those exist, but they don't exist
    # yet at build time (CLAUDE.md's "no tests during build" waiver), so
    # this is the one runnable check for now -- also exercises every
    # exception class in exceptions/__init__.py via TopicCoveredService's
    # own import chain.
    from unittest.mock import Mock

    from api.models.foundations.topic_covered.exceptions import TopicCoveredValidationException
    from api.services.foundations.topic_covered import TopicCoveredService

    broker = Mock()
    service = TopicCoveredService(broker, logging_broker=Mock())

    for bad_value in (None, "", "   "):
        try:
            service.create(1, bad_value)
            raise AssertionError(f"expected rejection for {bad_value!r}")
        except TopicCoveredValidationException:
            pass
    assert broker.insert.call_count == 0, "broker must not be called on invalid input"

    broker.insert.return_value = TopicCovered(
        id=1, profile_id=1, topic="preterite-vs-imperfect", first_covered_at=None, last_practiced_at=None
    )
    created = service.create(1, "preterite-vs-imperfect")
    assert created.topic == "preterite-vs-imperfect"
    broker.insert.assert_called_once_with(1, "preterite-vs-imperfect")

    broker.select_by_profile.return_value = [created]
    assert service.list_by_profile(1) == [created]

    broker.touch.return_value = created
    assert service.touch(1) == created

    print("topic_covered_service self-check passed")
