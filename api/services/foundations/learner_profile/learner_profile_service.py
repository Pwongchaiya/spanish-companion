"""Foundation service for the singleton learner_profile row.

Wraps ILearnerProfileBroker (api/brokers/learner_profile/) with input
validation only -- pure CRUD, no upsert, no get-or-create. ensure_profile()
(find-or-create the singleton) is Processing-tier logic per CLAUDE.md's
Processing-row reversal and the entity doc
(Projects/spanish-companion/entities/learner-profile.md).

Single broker dependency -> Foundation layer, not Orchestration, per
CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers.

Split into a base logic file plus Validations/Exceptions mixins (this file,
learner_profile_service_validations.py, learner_profile_service_exceptions.py),
combined into the concrete LearnerProfileService in __init__.py -- mirrors
C#'s `partial class` merging multiple files into one class
(python-adaptations-skill.md's Architecture Patterns table), the same
pattern used for Session Lifecycle and Flag in this codebase.
"""

from api.brokers.learner_profile import ILearnerProfileBroker
from api.brokers.logging import LoggingBroker
from api.models.foundations.learner_profile.exceptions import (
    LearnerProfileUnavailableError,
    NotFoundLearnerProfileException,
)
from api.models.foundations.learner_profile.learner_profile import LearnerProfile


class _LearnerProfileServiceBase:
    """Owns LearnerProfile CRUD.

    Public methods delegate to a private `_do_thing` method through
    `_try_catch` (defined in the Exceptions mixin), per python-adaptations-
    skill.md's TryCatch translation. Validation checks are named methods
    (defined in the Validations mixin) rather than inlined.
    """

    def __init__(
        self,
        broker: ILearnerProfileBroker,
        *,
        logging_broker: LoggingBroker,
    ) -> None:
        self._broker = broker
        self._logging_broker = logging_broker

    def create_profile(self, proficiency_level: str) -> LearnerProfile:
        return self._try_catch(lambda: self._create_profile(proficiency_level))

    def _create_profile(self, proficiency_level: str) -> LearnerProfile:
        self._validate_proficiency_level(proficiency_level)
        try:
            return self._broker.insert_profile(proficiency_level)
        except Exception as e:
            raise LearnerProfileUnavailableError(str(e)) from e

    def get_profile(self) -> LearnerProfile:
        return self._try_catch(self._get_profile)

    def _get_profile(self) -> LearnerProfile:
        try:
            profile = self._broker.select_profile()
        except Exception as e:
            raise LearnerProfileUnavailableError(str(e)) from e
        if profile is None:
            raise NotFoundLearnerProfileException()
        return profile

    def update_proficiency_level(self, profile_id: int, proficiency_level: str) -> LearnerProfile:
        return self._try_catch(lambda: self._update_proficiency_level(profile_id, proficiency_level))

    def _update_proficiency_level(self, profile_id: int, proficiency_level: str) -> LearnerProfile:
        self._validate_proficiency_level(proficiency_level)
        try:
            return self._broker.update_profile(profile_id, proficiency_level)
        except Exception as e:
            raise LearnerProfileUnavailableError(str(e)) from e


if __name__ == "__main__":
    # ponytail: self-check for the one branch worth testing without a live
    # broker/DB -- validation rejects blank/None input before ever reaching
    # the broker. Full behaviour (broker success/failure paths) is covered
    # by the Test Writer Agent's suite; this project's Phase 2 test strategy
    # has no separate assert-based check requirement once those exist, but
    # they don't exist yet at build time (CLAUDE.md's "no tests during
    # build" waiver), so this is the one runnable check for now.
    from unittest.mock import Mock

    from api.services.foundations.learner_profile import LearnerProfileService
    from api.models.foundations.learner_profile.exceptions import LearnerProfileValidationException

    broker = Mock()
    service = LearnerProfileService(broker, logging_broker=Mock())

    for bad_value in (None, "", "   "):
        try:
            service.create_profile(bad_value)
            raise AssertionError(f"expected rejection for {bad_value!r}")
        except LearnerProfileValidationException:
            pass
    assert broker.insert_profile.call_count == 0, "broker must not be called on invalid input"

    broker.insert_profile.return_value = LearnerProfile(id=1, proficiency_level="A2", updated_at=None)
    created = service.create_profile("A2")
    assert created.proficiency_level == "A2"
    broker.insert_profile.assert_called_once_with("A2")

    print("learner_profile_service self-check passed")
