"""Foundation service for the topic_covered entity.

Wraps ITopicCoveredBroker (api/brokers/topic_covered/) with input
validation only -- pure CRUD, no upsert, no find-by-topic.
record_topic()/`resolve()`-style logic (find-or-touch-or-create) is
Processing-tier logic per CLAUDE.md's Processing-row reversal and the
entity doc (Projects/spanish-companion/entities/topic-covered.md).

Single broker dependency -> Foundation layer, not Orchestration, per
CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers.

Split into a base logic file plus Validations/Exceptions mixins (this file,
topic_covered_service_validations.py, topic_covered_service_exceptions.py)
-- mirrors C#'s `partial class` merging UserProfileService.cs /
.Validations.cs / .Exceptions.cs into one class, via the
MistakePatternService precedent. Unlike C# (which reuses the same class
name across every partial file), Python has no `partial`, so the concrete
class is declared directly in THIS file, inheriting the other two mixins by
name -- no separate "_Base" intermediate class, no composition step in
__init__.py.

Public methods are the ONLY thing that wraps with `_try_catch` (defined in
the Exceptions mixin) -- mirrors UserProfileService.cs's actual shape
(NL.Core.Users, Services/Foundations/UserProfiles/UserProfileService.cs:
31-66): each public method's entire body -- validate, then call the broker
-- is an inline nested closure passed straight to `_try_catch`, not a
separate `_do_thing` private method. No local try/except inside the
closures: every exception -- domain leaf, raw SQLAlchemy, or otherwise --
propagates untouched to `_try_catch`, the single dispatch point that
classifies and wraps. `touch_topic_covered`'s None-check is not exception
handling: it's a business check on a normal return value, the same shape
as `UserProfileService.cs:42-53`'s `ValidateUserProfileExists` check on
`SelectUserProfileByIdAsync`'s result.
"""

from api.brokers.logging import LoggingBroker
from api.brokers.topic_covered.i_topic_covered_broker import ITopicCoveredBroker
from api.models.foundations.topic_covered.exceptions import NotFoundTopicCoveredException
from api.models.foundations.topic_covered.topic_covered import TopicCovered
from api.services.foundations.topic_covered.i_topic_covered_service import ITopicCoveredService
from api.services.foundations.topic_covered.topic_covered_service_exceptions import (
    TopicCoveredServiceExceptions,
)
from api.services.foundations.topic_covered.topic_covered_service_validations import (
    TopicCoveredServiceValidations,
)


class TopicCoveredService(
    TopicCoveredServiceExceptions,
    TopicCoveredServiceValidations,
    ITopicCoveredService,
):
    """Owns TopicCovered CRUD. Validation checks are named methods
    (defined in the Validations mixin) rather than inlined.
    """

    def __init__(
        self,
        topic_covered_broker: ITopicCoveredBroker,
        *,
        logging_broker: LoggingBroker,
    ) -> None:
        self._topic_covered_broker = topic_covered_broker
        self._logging_broker = logging_broker

    def list_topic_covered_by_profile(self, profile_id: int) -> list[TopicCovered]:
        def action() -> list[TopicCovered]:
            self._validate_topic_covered_on_list_by_profile(profile_id)
            return self._topic_covered_broker.select_topic_covered_by_profile(profile_id)

        return self._try_catch(action)

    def create_topic_covered(self, profile_id: int, topic: str) -> TopicCovered:
        def action() -> TopicCovered:
            self._validate_topic_covered_on_create(profile_id, topic)
            return self._topic_covered_broker.insert_topic_covered(profile_id, topic)

        return self._try_catch(action)

    def touch_topic_covered(self, topic_id: int) -> TopicCovered:
        def action() -> TopicCovered:
            self._validate_topic_covered_on_touch(topic_id)
            maybe_topic_covered = self._topic_covered_broker.touch_topic_covered(topic_id)
            if maybe_topic_covered is None:
                raise NotFoundTopicCoveredException()
            return maybe_topic_covered

        return self._try_catch(action)
