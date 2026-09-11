"""Relocated from learner_profile_service.py's __main__ self-check --
production files don't carry test code, matching NL.Core.Users.Api.Tests.Unit
being a separate tree from NL.Core.Users.Api, and mirroring
tests/unit/services/mistake_pattern/test_mistake_pattern_service.py's shape.
Expanded past the original single-field check for the renamed methods,
batched validation on update_learner_profile, and the NotFound-on-update
path (the previous broker crashed with AttributeError on a missing
profile_id instead of returning None cleanly -- see learner_profile_broker.py).
"""

from unittest.mock import Mock

from sqlalchemy.exc import OperationalError

from api.models.foundations.learner_profile.exceptions import (
    LearnerProfileDependencyException,
    LearnerProfileValidationException,
    NotFoundLearnerProfileException,
)
from api.models.foundations.learner_profile.learner_profile import LearnerProfile
from api.services.foundations.learner_profile import LearnerProfileService


def test_learner_profile_service():
    broker = Mock()
    service = LearnerProfileService(broker, logging_broker=Mock())

    for bad_value in (None, "", "   "):
        try:
            service.create_learner_profile(bad_value)
            raise AssertionError(f"expected rejection for {bad_value!r}")
        except LearnerProfileValidationException:
            pass
    assert broker.insert_learner_profile.call_count == 0, "broker must not be called on invalid input"

    for bad_id, bad_level in ((0, "A2"), (1, "")):
        try:
            service.update_learner_profile(bad_id, bad_level)
            raise AssertionError(f"expected rejection for ({bad_id!r}, {bad_level!r})")
        except LearnerProfileValidationException:
            pass
    assert broker.update_learner_profile.call_count == 0, "broker must not be called on invalid update input"

    # both fields bad at once -> both reported together, not fail-fast on
    # the first one (batched validation).
    try:
        service.update_learner_profile(0, "")
        raise AssertionError("expected rejection for all-fields-bad update")
    except LearnerProfileValidationException as e:
        leaf = e.inner_exception
        assert set(leaf.errors) == {"profile_id", "proficiency_level"}, (
            f"expected both fields reported together, got {set(leaf.errors)!r}"
        )

    broker.insert_learner_profile.return_value = LearnerProfile(id=1, proficiency_level="A2", updated_at=None)
    created = service.create_learner_profile("A2")
    assert created.proficiency_level == "A2"
    broker.insert_learner_profile.assert_called_once_with("A2")

    # get_learner_profile: no row yet -> NotFound, wrapped as validation
    broker.select_learner_profile.return_value = None
    try:
        service.get_learner_profile()
        raise AssertionError("expected NotFoundLearnerProfileException when no profile row exists")
    except LearnerProfileValidationException as e:
        assert isinstance(e.inner_exception, NotFoundLearnerProfileException)

    broker.select_learner_profile.return_value = LearnerProfile(id=1, proficiency_level="A2", updated_at=None)
    fetched = service.get_learner_profile()
    assert fetched.proficiency_level == "A2"

    # update_learner_profile: broker returns None for a missing profile_id
    # -> a clean NotFound, not a crash (the bug this rebuild fixes).
    broker.update_learner_profile.return_value = None
    try:
        service.update_learner_profile(999, "B1")
        raise AssertionError("expected NotFoundLearnerProfileException for a missing profile_id")
    except LearnerProfileValidationException as e:
        assert isinstance(e.inner_exception, NotFoundLearnerProfileException)

    broker.update_learner_profile.return_value = LearnerProfile(id=1, proficiency_level="B1", updated_at=None)
    updated = service.update_learner_profile(1, "B1")
    assert updated.proficiency_level == "B1"
    broker.update_learner_profile.assert_called_with(1, "B1")

    # any raw SQLAlchemy failure (e.g. connection refused) -> a dependency
    # failure, not the catch-all service exception -- the broker does no
    # wrapping of its own, so this has to be _try_catch's job.
    broker2 = Mock()
    broker2.select_learner_profile.side_effect = OperationalError("SELECT", {}, Exception("connection refused"))
    service2 = LearnerProfileService(broker2, logging_broker=Mock())
    try:
        service2.get_learner_profile()
        raise AssertionError("expected a dependency exception for a connection failure")
    except LearnerProfileDependencyException:
        pass
