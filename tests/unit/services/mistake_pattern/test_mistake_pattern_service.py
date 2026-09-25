"""Relocated from mistake_pattern_service.py's __main__ self-check --
production files don't carry test code, matching NL.Core.Users.Api.Tests.Unit
being a separate tree from NL.Core.Users.Api. Not split into the full
pytest 3-tier convention yet (per CLAUDE.md's deferred test-writing pass);
this is the same assert content, just moved to where it belongs.
"""

from unittest.mock import Mock

from sqlalchemy.exc import IntegrityError, OperationalError

from api.models.foundations.mistake_pattern.exceptions import (
    AlreadyExistsMistakePatternException,
    MistakePatternDependencyException,
    MistakePatternDependencyValidationException,
    MistakePatternValidationException,
    NotFoundMistakePatternException,
)
from api.models.foundations.mistake_pattern.mistake_pattern import MistakePattern
from api.services.foundations.mistake_pattern import MistakePatternService


def test_mistake_pattern_service():
    broker = Mock()
    service = MistakePatternService(broker, logging_broker=Mock())

    for bad_profile_id in (None, 0, -1):
        try:
            service.list_mistake_patterns_by_profile(bad_profile_id)
            raise AssertionError(f"expected rejection for profile_id={bad_profile_id!r}")
        except MistakePatternValidationException:
            pass
    assert broker.select_mistake_patterns_by_profile.call_count == 0, "broker must not be called on invalid profile_id"

    for bad_category in (None, "", "   "):
        try:
            service.create_mistake_pattern(1, bad_category)
            raise AssertionError(f"expected rejection for category={bad_category!r}")
        except MistakePatternValidationException:
            pass
    assert broker.insert_mistake_pattern.call_count == 0, "broker must not be called on invalid category"

    for bad_count, bad_status in ((0, "active"), (1, "done")):
        try:
            service.update_mistake_pattern(1, bad_count, bad_status)
            raise AssertionError(f"expected rejection for ({bad_count!r}, {bad_status!r})")
        except MistakePatternValidationException:
            pass
    assert broker.update_mistake_pattern.call_count == 0, "broker must not be called on invalid update input"

    try:
        service.update_mistake_pattern(0, 0, "done")
        raise AssertionError("expected rejection for all-three-fields-bad update")
    except MistakePatternValidationException as e:
        leaf = e.inner_exception
        assert set(leaf.errors) == {
            "pattern_id",
            "occurrence_count",
            "status",
        }, f"expected all 3 fields reported together, got {set(leaf.errors)!r}"

    broker.insert_mistake_pattern.return_value = MistakePattern(
        id=1, profile_id=1, category="ser vs estar", occurrence_count=1, last_seen_at=None, status="active"
    )
    created = service.create_mistake_pattern(1, "ser vs estar")
    assert created.category == "ser vs estar"
    broker.insert_mistake_pattern.assert_called_once_with(1, "ser vs estar")

    broker.update_mistake_pattern.return_value = None
    try:
        service.update_mistake_pattern(999, 1, "active")
        raise AssertionError("expected NotFoundMistakePatternException for a missing pattern_id")
    except MistakePatternValidationException as e:
        assert isinstance(e.inner_exception, NotFoundMistakePatternException)

    # a unique-constraint violation on create() -> AlreadyExists, not a
    # generic "unavailable" -- the race between Processing's find-by-category
    # check and create() actually inserting.
    broker2 = Mock()
    broker2.insert_mistake_pattern.side_effect = IntegrityError(
        "INSERT",
        {},
        Exception('duplicate key value violates unique constraint "mistake_pattern_profile_id_category_key"'),
    )
    service2 = MistakePatternService(broker2, logging_broker=Mock())
    try:
        service2.create_mistake_pattern(1, "ser vs estar")
        raise AssertionError("expected AlreadyExistsMistakePatternException for a duplicate (profile_id, category)")
    except MistakePatternDependencyValidationException as e:
        assert isinstance(e.inner_exception, AlreadyExistsMistakePatternException)

    # a non-unique integrity failure still falls through to the generic
    # dependency path, not AlreadyExists.
    broker3 = Mock()
    broker3.insert_mistake_pattern.side_effect = IntegrityError(
        "INSERT", {}, Exception("NOT NULL constraint failed: category")
    )
    service3 = MistakePatternService(broker3, logging_broker=Mock())
    try:
        service3.create_mistake_pattern(1, "ser vs estar")
        raise AssertionError("expected a generic dependency exception for a non-unique integrity failure")
    except MistakePatternDependencyValidationException:
        raise AssertionError("a NOT NULL violation must not be classified as AlreadyExists")
    except Exception as e:
        assert type(e).__name__ == "MistakePatternDependencyException", type(e).__name__

    # any other raw SQLAlchemy failure (e.g. connection refused) -> a
    # dependency failure, not the catch-all service exception -- the broker
    # does no wrapping of its own, so this has to be _try_catch's job.
    broker4 = Mock()
    broker4.select_mistake_patterns_by_profile.side_effect = OperationalError(
        "SELECT", {}, Exception("connection refused")
    )
    service4 = MistakePatternService(broker4, logging_broker=Mock())
    try:
        service4.list_mistake_patterns_by_profile(1)
        raise AssertionError("expected a dependency exception for a connection failure")
    except MistakePatternDependencyException:
        pass
