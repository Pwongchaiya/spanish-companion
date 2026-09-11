"""Validation checks for LearnerProfileService.

Mirrors ConversationSessionServiceValidations's shape -- a private method
containing a single `if (condition): raise LeafException()` check, called
from the base service file's public-method bodies rather than inlined
there.
"""

from api.models.foundations.learner_profile.exceptions import InvalidLearnerProfileInputError


class LearnerProfileServiceValidations:
    """Mixin: raises the leaf exceptions when input doesn't pass checks.
    See learner_profile_service_exceptions.py for how these get wrapped and
    logged before leaving the service.
    """

    def _validate_proficiency_level(self, proficiency_level: str | None) -> None:
        if proficiency_level is None or not proficiency_level.strip():
            raise InvalidLearnerProfileInputError(proficiency_level)
