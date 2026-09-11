"""Processing service for the singleton learner_profile row.

Higher-order logic on top of the single Foundation dependency
(ILearnerProfileService): get-or-create the singleton profile row.
Foundation stays pure CRUD (see learner_profile_service.py's docstring) --
this is exactly the composition the Processing tier exists for per
CLAUDE.md's Processing-row reversal and the entity doc
(Projects/spanish-companion/entities/learner-profile.md).

One method -> no base/validations/exceptions mixin split (that split earns
its keep once there's more than one method to organise; see Foundation's
three-file layout for when it does -- same call made for
MistakePatternProcessingService).
"""

from api.models.foundations.learner_profile.exceptions import LearnerProfileValidationException
from api.models.foundations.learner_profile.learner_profile import LearnerProfile
from api.services.foundations.learner_profile.i_learner_profile_service import ILearnerProfileService


class LearnerProfileProcessingService:
    """Combines Foundation's get_learner_profile() + create_learner_profile()
    into a single get-or-create call. Do-or-delegate: this method decides
    which Foundation call to make, then delegates entirely -- it never
    transforms the result.
    """

    def __init__(self, learner_profile_service: ILearnerProfileService) -> None:
        self._learner_profile_service = learner_profile_service

    def ensure_profile(self, default_level: str) -> LearnerProfile:
        try:
            return self._learner_profile_service.get_learner_profile()
        except LearnerProfileValidationException:
            # ponytail: get_learner_profile() takes no args, so the only
            # cause of LearnerProfileValidationException here is
            # Foundation's not-found signal (NotFoundLearnerProfileException
            # wrapped) -- no inner_exception discrimination needed. If
            # Foundation later adds another get_learner_profile() validation
            # cause, narrow this catch then.
            return self._learner_profile_service.create_learner_profile(default_level)
