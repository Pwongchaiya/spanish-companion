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
mistake_pattern_service_validations.py, mistake_pattern_service_exceptions.py)
-- mirrors C#'s `partial class` merging UserProfileService.cs /
.Validations.cs / .Exceptions.cs into one class. Unlike C# (which reuses the
same class name, `UserProfileService`, across every partial file), Python
has no `partial`, so the concrete class is declared directly in THIS file,
inheriting the other two mixins by name -- no separate "_Base" intermediate
class, no composition step in __init__.py. Matches the already-Python
CalendlyInviteeFoundationService precedent's shape exactly: one class,
declared once, `class X(XExceptions, XValidations, IX):`, constructor and
public methods on it directly.

Public methods are the ONLY thing that wraps with `_try_catch` (defined in
the Exceptions mixin) -- mirrors UserProfileService.cs's actual shape
(NL.Core.Users, Services/Foundations/UserProfiles/UserProfileService.cs:
31-66): each public method's entire body -- validate, then call the broker
-- is an inline nested closure passed straight to `_try_catch`, not a
separate `_do_thing` private method. No local try/except inside the
closures: every exception -- domain leaf, raw SQLAlchemy, or otherwise --
propagates untouched to `_try_catch`, the single dispatch point that
classifies and wraps. `update`'s None-check is not exception handling:
it's a business check on a normal return value, the same shape as
`UserProfileService.cs:42-53`'s `ValidateUserProfileExists` check on
`SelectUserProfileByIdAsync`'s result.
"""

from api.brokers.logging import LoggingBroker
from api.brokers.mistake_pattern.i_mistake_pattern_broker import IMistakePatternBroker
from api.models.foundations.mistake_pattern.exceptions import NotFoundMistakePatternException
from api.models.foundations.mistake_pattern.mistake_pattern import MistakePattern
from api.services.foundations.mistake_pattern.i_mistake_pattern_service import IMistakePatternService
from api.services.foundations.mistake_pattern.mistake_pattern_service_exceptions import (
    MistakePatternServiceExceptions,
)
from api.services.foundations.mistake_pattern.mistake_pattern_service_validations import (
    MistakePatternServiceValidations,
)


class MistakePatternService(
    MistakePatternServiceExceptions,
    MistakePatternServiceValidations,
    IMistakePatternService,
):
    """Owns MistakePattern CRUD. Validation checks are named methods
    (defined in the Validations mixin) rather than inlined.
    """

    def __init__(
        self,
        mistake_pattern_broker: IMistakePatternBroker,
        *,
        logging_broker: LoggingBroker,
    ) -> None:
        self._mistake_pattern_broker = mistake_pattern_broker
        self._logging_broker = logging_broker

    def list_mistake_patterns_by_profile(self, profile_id: int) -> list[MistakePattern]:
        def action() -> list[MistakePattern]:
            self._validate_mistake_pattern_on_list_by_profile(profile_id)
            return self._mistake_pattern_broker.select_mistake_patterns_by_profile(profile_id)

        return self._try_catch(action)

    def create_mistake_pattern(self, profile_id: int, category: str) -> MistakePattern:
        def action() -> MistakePattern:
            self._validate_mistake_pattern_on_create(profile_id, category)
            return self._mistake_pattern_broker.insert_mistake_pattern(profile_id, category)

        return self._try_catch(action)

    def update_mistake_pattern(self, pattern_id: int, occurrence_count: int, status: str) -> MistakePattern:
        def action() -> MistakePattern:
            self._validate_mistake_pattern_on_update(pattern_id, occurrence_count, status)
            maybe_mistake_pattern = self._mistake_pattern_broker.update_mistake_pattern(
                pattern_id, occurrence_count, status
            )
            if maybe_mistake_pattern is None:
                raise NotFoundMistakePatternException()
            return maybe_mistake_pattern

        return self._try_catch(action)
