"""Foundation service for the singleton learner_profile row.

Wraps ILearnerProfileBroker (api/brokers/learner_profile/) with input
validation only -- pure CRUD, no upsert, no get-or-create. ensure_profile()
(find-or-create the singleton) is Processing-tier logic per CLAUDE.md's
Processing-row reversal and the entity doc
(Projects/spanish-companion/entities/learner-profile.md).

Single broker dependency -> Foundation layer, not Orchestration, per
CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers.

Split into a base logic file plus Validations/Exceptions mixins (this file,
learner_profile_service_validations.py, learner_profile_service_exceptions.py)
-- mirrors C#'s `partial class` merging UserProfileService.cs /
.Validations.cs / .Exceptions.cs into one class. Unlike C# (which reuses the
same class name across every partial file), Python has no `partial`, so the
concrete class is declared directly in THIS file, inheriting the other two
mixins by name -- no separate "_Base" intermediate class, no composition
step in __init__.py. Matches MistakePatternService's rebuilt shape exactly:
one class, declared once, `class X(XExceptions, XValidations, IX):`,
constructor and public methods on it directly. (The previous
`_LearnerProfileServiceBase` + __init__.py composition step was the
invented-`_ServiceBase` pattern CLAUDE.md explicitly disallows -- removed.)

Public methods are the ONLY thing that wraps with `_try_catch` (defined in
the Exceptions mixin) -- mirrors UserProfileService.cs's actual shape
(NL.Core.Users, Services/Foundations/UserProfiles/UserProfileService.cs:
31-66): each public method's entire body -- validate, then call the broker
-- is an inline nested closure passed straight to `_try_catch`, not a
separate `_do_thing` private method (the previous per-method
`_create_profile`/`_get_profile`/inline try/except indirection is removed).
No local try/except inside the closures: every exception -- domain leaf, raw
SQLAlchemy, or otherwise -- propagates untouched to `_try_catch`, the single
dispatch point that classifies and wraps. update_learner_profile's
None-check is not exception handling: it's a business check on a normal
return value, the same shape as `UserProfileService.cs:42-53`'s
`ValidateUserProfileExists` check on `SelectUserProfileByIdAsync`'s result,
and the fix for this entity's previous bug (the broker crashed with an
AttributeError on a missing profile_id instead of returning None cleanly --
see learner_profile_broker.py).

Method names embed the entity name (create_learner_profile,
get_learner_profile, update_learner_profile), matching NL.Core.Users'
Service interface methods (AddUserProfileAsync, RetrieveUserProfileByIdAsync,
ModifyUserProfileAsync -- IUserProfileService.cs) the same way already
applied to MistakePatternService -- the previous create_profile/get_profile/
update_proficiency_level names dropped "learner" from the entity name.

No AlreadyExists/DependencyValidation exception tier, unlike
MistakePatternService -- see learner_profile_service_exceptions.py's
docstring for why.
"""

from api.brokers.learner_profile.i_learner_profile_broker import ILearnerProfileBroker
from api.brokers.logging import LoggingBroker
from api.models.foundations.learner_profile.exceptions import NotFoundLearnerProfileException
from api.models.foundations.learner_profile.learner_profile import LearnerProfile
from api.services.foundations.learner_profile.i_learner_profile_service import ILearnerProfileService
from api.services.foundations.learner_profile.learner_profile_service_exceptions import (
    LearnerProfileServiceExceptions,
)
from api.services.foundations.learner_profile.learner_profile_service_validations import (
    LearnerProfileServiceValidations,
)


class LearnerProfileService(
    LearnerProfileServiceExceptions,
    LearnerProfileServiceValidations,
    ILearnerProfileService,
):
    """Owns LearnerProfile CRUD. Validation checks are named methods
    (defined in the Validations mixin) rather than inlined.
    """

    def __init__(
        self,
        learner_profile_broker: ILearnerProfileBroker,
        *,
        logging_broker: LoggingBroker,
    ) -> None:
        self._learner_profile_broker = learner_profile_broker
        self._logging_broker = logging_broker

    def create_learner_profile(self, proficiency_level: str) -> LearnerProfile:
        def action() -> LearnerProfile:
            self._validate_learner_profile_on_create(proficiency_level)
            return self._learner_profile_broker.insert_learner_profile(proficiency_level)

        return self._try_catch(action)

    def get_learner_profile(self) -> LearnerProfile:
        def action() -> LearnerProfile:
            maybe_learner_profile = self._learner_profile_broker.select_learner_profile()
            if maybe_learner_profile is None:
                raise NotFoundLearnerProfileException()
            return maybe_learner_profile

        return self._try_catch(action)

    def update_learner_profile(self, profile_id: int, proficiency_level: str) -> LearnerProfile:
        def action() -> LearnerProfile:
            self._validate_learner_profile_on_update(profile_id, proficiency_level)
            maybe_learner_profile = self._learner_profile_broker.update_learner_profile(
                profile_id, proficiency_level
            )
            if maybe_learner_profile is None:
                raise NotFoundLearnerProfileException()
            return maybe_learner_profile

        return self._try_catch(action)
