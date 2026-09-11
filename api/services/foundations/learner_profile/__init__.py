from api.services.foundations.learner_profile.i_learner_profile_service import ILearnerProfileService
from api.services.foundations.learner_profile.learner_profile_service import _LearnerProfileServiceBase
from api.services.foundations.learner_profile.learner_profile_service_validations import (
    LearnerProfileServiceValidations,
)
from api.services.foundations.learner_profile.learner_profile_service_exceptions import (
    LearnerProfileServiceExceptions,
)


class LearnerProfileService(
    _LearnerProfileServiceBase,
    LearnerProfileServiceValidations,
    LearnerProfileServiceExceptions,
):
    """Combines the base logic, validations, and exceptions mixins into the
    concrete Foundation service -- mirrors C#'s `partial class` merging
    EntitlementService.cs / .Validations.cs / .Exeptions.cs into one class,
    the same multi-inheritance-merge already used for Session Lifecycle in
    this codebase.
    """


__all__ = [
    "ILearnerProfileService",
    "LearnerProfileService",
]
