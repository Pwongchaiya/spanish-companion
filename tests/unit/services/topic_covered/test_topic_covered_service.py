"""Relocated from topic_covered_service.py's __main__ self-check --
production files don't carry test code, matching NL.Core.Users.Api.Tests.Unit
being a separate tree from NL.Core.Users.Api. Mirrors
tests/unit/services/mistake_pattern/test_mistake_pattern_service.py's shape,
extended for TopicCovered's touch_topic_covered NotFound path and the
create_topic_covered AlreadyExists race.
"""

from unittest.mock import Mock

from sqlalchemy.exc import IntegrityError, OperationalError

from api.models.foundations.topic_covered.exceptions import (
    AlreadyExistsTopicCoveredException,
    TopicCoveredDependencyException,
    TopicCoveredDependencyValidationException,
    TopicCoveredValidationException,
    NotFoundTopicCoveredException,
)
from api.models.foundations.topic_covered.topic_covered import TopicCovered
from api.services.foundations.topic_covered import TopicCoveredService


def test_topic_covered_service():
    broker = Mock()
    service = TopicCoveredService(broker, logging_broker=Mock())

    for bad_profile_id in (None, 0, -1):
        try:
            service.list_topic_covered_by_profile(bad_profile_id)
            raise AssertionError(f"expected rejection for profile_id={bad_profile_id!r}")
        except TopicCoveredValidationException:
            pass
    assert broker.select_topic_covered_by_profile.call_count == 0, "broker must not be called on invalid profile_id"

    for bad_topic in (None, "", "   "):
        try:
            service.create_topic_covered(1, bad_topic)
            raise AssertionError(f"expected rejection for topic={bad_topic!r}")
        except TopicCoveredValidationException:
            pass
    assert broker.insert_topic_covered.call_count == 0, "broker must not be called on invalid topic"

    for bad_topic_id in (None, 0, -1):
        try:
            service.touch_topic_covered(bad_topic_id)
            raise AssertionError(f"expected rejection for topic_id={bad_topic_id!r}")
        except TopicCoveredValidationException:
            pass
    assert broker.touch_topic_covered.call_count == 0, "broker must not be called on invalid topic_id"

    try:
        service.create_topic_covered(0, "")
        raise AssertionError("expected rejection for all-fields-bad create")
    except TopicCoveredValidationException as e:
        leaf = e.inner_exception
        assert set(leaf.errors) == {"profile_id", "topic"}, (
            f"expected both fields reported together, got {set(leaf.errors)!r}"
        )

    broker.insert_topic_covered.return_value = TopicCovered(
        id=1, profile_id=1, topic="preterite-vs-imperfect", first_covered_at=None, last_practiced_at=None
    )
    created = service.create_topic_covered(1, "preterite-vs-imperfect")
    assert created.topic == "preterite-vs-imperfect"
    broker.insert_topic_covered.assert_called_once_with(1, "preterite-vs-imperfect")

    broker.select_topic_covered_by_profile.return_value = [created]
    assert service.list_topic_covered_by_profile(1) == [created]

    # touch: found -> broker returns the touched row
    broker.touch_topic_covered.return_value = created
    assert service.touch_topic_covered(1) == created

    # touch: missing id -> broker returns None -> NotFoundTopicCoveredException
    broker.touch_topic_covered.return_value = None
    try:
        service.touch_topic_covered(999)
        raise AssertionError("expected NotFoundTopicCoveredException for a missing topic_id")
    except TopicCoveredValidationException as e:
        assert isinstance(e.inner_exception, NotFoundTopicCoveredException)

    # a unique-constraint violation on create_topic_covered() -> AlreadyExists,
    # not a generic "unavailable" -- the race between Processing's
    # find-by-topic check and create_topic_covered() actually inserting.
    broker2 = Mock()
    broker2.insert_topic_covered.side_effect = IntegrityError(
        "INSERT", {}, Exception('duplicate key value violates unique constraint "uq_topic_covered_profile_topic"')
    )
    service2 = TopicCoveredService(broker2, logging_broker=Mock())
    try:
        service2.create_topic_covered(1, "preterite-vs-imperfect")
        raise AssertionError("expected AlreadyExistsTopicCoveredException for a duplicate (profile_id, topic)")
    except TopicCoveredDependencyValidationException as e:
        assert isinstance(e.inner_exception, AlreadyExistsTopicCoveredException)

    # a non-unique integrity failure still falls through to the generic
    # dependency path, not AlreadyExists.
    broker3 = Mock()
    broker3.insert_topic_covered.side_effect = IntegrityError("INSERT", {}, Exception("NOT NULL constraint failed: topic"))
    service3 = TopicCoveredService(broker3, logging_broker=Mock())
    try:
        service3.create_topic_covered(1, "preterite-vs-imperfect")
        raise AssertionError("expected a generic dependency exception for a non-unique integrity failure")
    except TopicCoveredDependencyValidationException:
        raise AssertionError("a NOT NULL violation must not be classified as AlreadyExists")
    except Exception as e:
        assert type(e).__name__ == "TopicCoveredDependencyException", type(e).__name__

    # any other raw SQLAlchemy failure (e.g. connection refused) -> a
    # dependency failure, not the catch-all service exception -- the broker
    # does no wrapping of its own, so this has to be _try_catch's job.
    broker4 = Mock()
    broker4.select_topic_covered_by_profile.side_effect = OperationalError("SELECT", {}, Exception("connection refused"))
    service4 = TopicCoveredService(broker4, logging_broker=Mock())
    try:
        service4.list_topic_covered_by_profile(1)
        raise AssertionError("expected a dependency exception for a connection failure")
    except TopicCoveredDependencyException:
        pass
