"""Relocated from learner_profile_processing_service.py's __main__
self-check -- production files don't carry test code, matching
NL.Core.Users.Api.Tests.Unit being a separate tree from NL.Core.Users.Api,
and tests/unit/services/mistake_pattern/test_mistake_pattern_processing_service.py's
shape. Adapted for the renamed get_learner_profile()/create_learner_profile()
Foundation calls.
"""

from unittest.mock import Mock

from api.models.foundations.learner_profile.exceptions import (
    LearnerProfileValidationException,
    NotFoundLearnerProfileException,
)
from api.models.foundations.learner_profile.learner_profile import LearnerProfile
from api.services.processings.learner_profile.learner_profile_processing_service import (
    LearnerProfileProcessingService,
)


def test_learner_profile_processing_service():
    existing = LearnerProfile(id=1, proficiency_level="A2", updated_at=None)
    foundation = Mock()
    foundation.get_learner_profile.return_value = existing
    service = LearnerProfileProcessingService(foundation)

    assert service.ensure_profile("A1") is existing
    foundation.create_learner_profile.assert_not_called()

    created = LearnerProfile(id=1, proficiency_level="A1", updated_at=None)
    foundation = Mock()
    foundation.get_learner_profile.side_effect = LearnerProfileValidationException(
        inner_exception=NotFoundLearnerProfileException()
    )
    foundation.create_learner_profile.return_value = created
    service = LearnerProfileProcessingService(foundation)

    assert service.ensure_profile("A1") is created
    foundation.create_learner_profile.assert_called_once_with("A1")
