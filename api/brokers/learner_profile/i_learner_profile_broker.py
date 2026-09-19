"""Broker interface for the singleton `learner_profile` row.

`typing.Protocol`, not `ABC` — per CLAUDE.md's Broker-interfaces waiver
(matches `NL.Core.Entitlements`'s `IEntitlementService.cs` sitting next to
its implementation, not the toolkit's ABC default). Pure CRUD only — no
upsert, no get-or-create. `ensure_profile()` (find-or-create the singleton)
is Processing-tier logic, built later against this interface.
"""

from typing import Optional, Protocol

from api.models.foundations.learner_profile.learner_profile import LearnerProfile


class ILearnerProfileBroker(Protocol):
    """External-resource boundary for `learner_profile` persistence. Raw
    SQLAlchemy CRUD only — no business logic, no exception handling.

    Method names embed the entity name (`insert_learner_profile`, not
    `insert`), matching NL.Core.Users' actual storage broker interface
    verbatim (`InsertUserProfileAsync`, `SelectUserProfileByIdAsync`,
    `UpdateUserProfileAsync` — IStorageBroker.UserProfiles.cs:14-17), same
    convention already applied to IMistakePatternBroker.
    """

    def select_learner_profile(self) -> LearnerProfile | None:
        """The one profile row, or None if it hasn't been created yet."""
        ...

    def insert_learner_profile(self, proficiency_level: str | None) -> LearnerProfile:
        """Insert a new profile row. Caller (Processing) is responsible for
        only ever calling this when select_learner_profile() returned None."""
        ...

    def update_learner_profile(
        self,
        profile_id: int,
        proficiency_level: str | None = None,
        cefr_estimate: str | None = None,
    ) -> Optional[LearnerProfile]:
        """Partial update: a field is only written when its argument is not
        None, so roadmap A6's CEFR-only write can't clobber proficiency_level
        (or vice versa). Returns None if profile_id doesn't exist —
        Foundation maps that to NotFoundLearnerProfileException, same
        convention as IMistakePatternBroker.update_mistake_pattern()."""
        ...
