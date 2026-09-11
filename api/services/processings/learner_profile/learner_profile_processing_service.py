"""Processing service for the singleton learner_profile row.

Higher-order logic on top of the single Foundation dependency
(ILearnerProfileService): get-or-create the singleton profile row.
Foundation stays pure CRUD (see learner_profile_service.py's docstring) --
this is exactly the composition the Processing tier exists for per
CLAUDE.md's Processing-row reversal and the entity doc
(Projects/spanish-companion/entities/learner-profile.md).

One method -> no base/validations/exceptions mixin split (that split earns
its keep once there's more than one method to organise; see Foundation's
three-file layout for when it does).
"""

from api.models.foundations.learner_profile.exceptions import LearnerProfileValidationException
from api.models.foundations.learner_profile.learner_profile import LearnerProfile
from api.services.foundations.learner_profile.i_learner_profile_service import ILearnerProfileService


class LearnerProfileProcessingService:
    """Combines Foundation's get_profile() + create_profile() into a single
    get-or-create call. Do-or-delegate: this method decides which Foundation
    call to make, then delegates entirely -- it never transforms the result.
    """

    def __init__(self, learner_profile_service: ILearnerProfileService) -> None:
        self._learner_profile_service = learner_profile_service

    def ensure_profile(self, default_level: str) -> LearnerProfile:
        try:
            return self._learner_profile_service.get_profile()
        except LearnerProfileValidationException:
            # ponytail: get_profile() takes no args, so the only cause of
            # LearnerProfileValidationException here is Foundation's
            # not-found signal (NotFoundLearnerProfileException wrapped) --
            # no inner_exception discrimination needed. If Foundation later
            # adds another get_profile() validation cause, narrow this catch
            # then.
            return self._learner_profile_service.create_profile(default_level)


if __name__ == "__main__":
    # ponytail: the one runnable check -- both branches of the get-or-create
    # decision, against a mocked Foundation service (per test-processing-
    # skill.md's "always mock Foundation" rule, done here as a lightweight
    # self-check since CLAUDE.md's "no tests during build" waiver applies).
    from unittest.mock import Mock

    from api.models.foundations.learner_profile.exceptions import NotFoundLearnerProfileException

    existing = LearnerProfile(id=1, proficiency_level="A2", updated_at=None)
    foundation = Mock()
    foundation.get_profile.return_value = existing
    service = LearnerProfileProcessingService(foundation)

    assert service.ensure_profile("A1") is existing
    foundation.create_profile.assert_not_called()

    created = LearnerProfile(id=1, proficiency_level="A1", updated_at=None)
    foundation = Mock()
    foundation.get_profile.side_effect = LearnerProfileValidationException(
        inner_exception=NotFoundLearnerProfileException()
    )
    foundation.create_profile.return_value = created
    service = LearnerProfileProcessingService(foundation)

    assert service.ensure_profile("A1") is created
    foundation.create_profile.assert_called_once_with("A1")

    print("learner_profile_processing_service self-check passed")
