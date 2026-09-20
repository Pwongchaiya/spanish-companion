"""IngestionQueueService (Foundation): validation, not-found, and exception wrapping."""

from datetime import datetime
from unittest.mock import Mock

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError

from api.brokers.ingestion_queue import IIngestionQueueBroker
from api.models.foundations.ingestion_queue.exceptions import (
    AlreadyExistsIngestionQueueException,
    IngestionQueueDependencyException,
    IngestionQueueDependencyValidationException,
    IngestionQueueServiceException,
    IngestionQueueValidationException,
    NotFoundIngestionQueueException,
)
from api.models.foundations.ingestion_queue.ingestion_queue import IngestionQueue
from api.services.foundations.ingestion_queue import IngestionQueueService

NOW = datetime(2026, 1, 2, 3, 4, 5)
TOPIC = "ser-vs-estar"


def make_row(count: int = 1, status: str = "pending") -> IngestionQueue:
    return IngestionQueue(
        id=1, topic=TOPIC, weak_verdict_count=count, status=status, first_flagged_at=NOW, last_flagged_at=NOW
    )


@pytest.fixture
def broker():
    return Mock(spec=IIngestionQueueBroker)


@pytest.fixture
def logging_broker():
    return Mock()


@pytest.fixture
def service(broker, logging_broker):
    return IngestionQueueService(broker, logging_broker=logging_broker)


class TestCreate:
    def test_should_insert_and_return_row_for_valid_topic(self, service, broker):
        broker.insert_ingestion_queue.return_value = make_row()
        assert service.create_ingestion_queue(TOPIC, 1, NOW) == make_row()
        broker.insert_ingestion_queue.assert_called_once_with(TOPIC, 1, NOW)

    @pytest.mark.parametrize("bad_topic", [None, "", "   ", "not-a-rae-topic"])
    def test_should_reject_topic_outside_topics_list(self, service, broker, bad_topic):
        with pytest.raises(IngestionQueueValidationException):
            service.create_ingestion_queue(bad_topic, 1, NOW)
        assert broker.insert_ingestion_queue.call_count == 0

    def test_should_report_every_bad_field_together(self, service):
        with pytest.raises(IngestionQueueValidationException) as info:
            service.create_ingestion_queue("nope", -1, NOW)
        assert set(info.value.inner_exception.errors) == {"topic", "weak_verdict_count"}

    def test_should_map_unique_violation_to_already_exists(self, service, broker):
        broker.insert_ingestion_queue.side_effect = IntegrityError(
            "INSERT", {}, Exception("UNIQUE constraint failed: ingestion_queue.topic")
        )
        with pytest.raises(IngestionQueueDependencyValidationException) as info:
            service.create_ingestion_queue(TOPIC, 1, NOW)
        assert isinstance(info.value.inner_exception, AlreadyExistsIngestionQueueException)

    def test_should_map_non_unique_integrity_failure_to_dependency(self, service, broker):
        broker.insert_ingestion_queue.side_effect = IntegrityError("INSERT", {}, Exception("NOT NULL failed"))
        with pytest.raises(IngestionQueueDependencyException):
            service.create_ingestion_queue(TOPIC, 1, NOW)


class TestUpdate:
    def test_should_update_and_return_row(self, service, broker):
        broker.update_ingestion_queue.return_value = make_row(2)
        assert service.update_ingestion_queue(1, 2, "pending", NOW) == make_row(2)
        broker.update_ingestion_queue.assert_called_once_with(1, 2, "pending", NOW)

    @pytest.mark.parametrize("queue_id,count,status", [(0, 1, "pending"), (1, -1, "pending"), (1, 1, "done")])
    def test_should_reject_bad_input_without_touching_broker(self, service, broker, queue_id, count, status):
        with pytest.raises(IngestionQueueValidationException):
            service.update_ingestion_queue(queue_id, count, status, NOW)
        assert broker.update_ingestion_queue.call_count == 0

    def test_should_raise_not_found_when_broker_returns_none(self, service, broker):
        broker.update_ingestion_queue.return_value = None
        with pytest.raises(IngestionQueueValidationException) as info:
            service.update_ingestion_queue(9, 1, "pending", NOW)
        assert isinstance(info.value.inner_exception, NotFoundIngestionQueueException)
        broker.update_ingestion_queue.assert_called_once()


class TestList:
    def test_should_return_all_rows(self, service, broker):
        broker.select_all_ingestion_queue.return_value = [make_row()]
        assert service.list_ingestion_queue() == [make_row()]
        broker.select_all_ingestion_queue.assert_called_once_with()

    def test_should_map_connection_failure_to_dependency_exception(self, service, broker, logging_broker):
        broker.select_all_ingestion_queue.side_effect = OperationalError("SELECT", {}, Exception("refused"))
        with pytest.raises(IngestionQueueDependencyException):
            service.list_ingestion_queue()
        assert logging_broker.log_error.call_count == 1

    def test_should_map_unexpected_failure_to_service_exception(self, service, broker):
        broker.select_all_ingestion_queue.side_effect = RuntimeError("boom")
        with pytest.raises(IngestionQueueServiceException):
            service.list_ingestion_queue()
