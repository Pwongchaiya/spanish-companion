"""Broker -> Foundation -> Processing against in-memory sqlite: upsert, threshold, UNIQUE(topic)."""

from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from api.brokers.ingestion_queue import SqlAlchemyIngestionQueueBroker
from api.models.base import Base
from api.models.foundations.ingestion_queue.exceptions import IngestionQueueDependencyValidationException
from api.models.foundations.ingestion_queue.ingestion_queue import IngestionQueueRecord
from api.services.foundations.ingestion_queue import IngestionQueueService
from api.services.processings.ingestion_queue import IngestionQueueProcessingService

T0 = datetime(2026, 1, 2, 3, 4, 5)


@pytest.fixture
def stack():
    broker = SqlAlchemyIngestionQueueBroker("sqlite:///:memory:")
    Base.metadata.create_all(broker._engine, tables=[IngestionQueueRecord.__table__])
    service = IngestionQueueService(broker, logging_broker=Mock())
    return service, IngestionQueueProcessingService(service)


def test_should_upsert_count_and_timestamps_then_surface_at_threshold_then_mark_ingested(stack):
    service, processing = stack

    for i in range(3):
        row = processing.record_weak_verdict("ser-vs-estar", T0 + timedelta(hours=i))

    assert row.weak_verdict_count == 3
    assert row.first_flagged_at == T0
    assert row.last_flagged_at == T0 + timedelta(hours=2)
    processing.record_weak_verdict("gender-agreement", T0)
    assert [r.topic for r in processing.list_pending(3)] == ["ser-vs-estar"]

    processing.mark_ingested("ser-vs-estar")
    assert processing.list_pending(3) == []
    assert len(service.list_ingestion_queue()) == 2


def test_should_reject_duplicate_topic_via_unique_constraint(stack):
    service, _ = stack
    service.create_ingestion_queue("ser-vs-estar", 1, T0)

    with pytest.raises(IngestionQueueDependencyValidationException):
        service.create_ingestion_queue("ser-vs-estar", 1, T0)
