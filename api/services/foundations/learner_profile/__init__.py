"""Re-exports the concrete LearnerProfileService class, declared directly in
learner_profile_service.py (which inherits the Validations/Exceptions mixins
by name) -- no composition step here, matching MistakePatternService's
rebuilt one-class-declared-once shape.
"""

from api.services.foundations.learner_profile.i_learner_profile_service import ILearnerProfileService
from api.services.foundations.learner_profile.learner_profile_service import LearnerProfileService

__all__ = [
    "ILearnerProfileService",
    "LearnerProfileService",
]
