"""IngestionQueueProcessingService: record_weak_verdict upsert, list_pending, mark_ingested."""

from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from api.models.foundations.ingestion_queue.exceptions import (
    IngestionQueueValidationException,
    NotFoundIngestionQueueException,
)
from api.models.foundations.ingestion_queue.ingestion_queue import IngestionQueue
from api.services.foundations.ingestion_queue import IIngestionQueueService
from api.services.processings.ingestion_queue import IngestionQueueProcessingService

FIRST = datetime(2026, 1, 2, 3, 4, 5)
NOW = FIRST + timedelta(days=1)


def make_row(topic="ser-vs-estar", count=1, status="pending", row_id=1) -> IngestionQueue:
    return IngestionQueue(
        id=row_id, topic=topic, weak_verdict_count=count, status=status, first_flagged_at=FIRST, last_flagged_at=FIRST
    )


@pytest.fixture
def foundation():
    return Mock(spec=IIngestionQueueService)


@pytest.fixture
def service(foundation):
    return IngestionQueueProcessingService(foundation)


class TestRecordWeakVerdict:
    def test_should_create_row_with_count_one_when_topic_is_new(self, service, foundation):
        foundation.list_ingestion_queue.return_value = [make_row(topic="gender-agreement")]
        foundation.create_ingestion_queue.return_value = make_row()

        actual = service.record_weak_verdict("ser-vs-estar", NOW)

        assert actual == make_row()
        foundation.create_ingestion_queue.assert_called_once_with("ser-vs-estar", 1, NOW)
        foundation.list_ingestion_queue.assert_called_once_with()
        assert foundation.update_ingestion_queue.call_count == 0

    def test_should_increment_count_and_bump_last_flagged_when_topic_exists(self, service, foundation):
        foundation.list_ingestion_queue.return_value = [make_row(count=2, row_id=7)]
        foundation.update_ingestion_queue.return_value = make_row(count=3, row_id=7)

        actual = service.record_weak_verdict("ser-vs-estar", NOW)

        assert actual.weak_verdict_count == 3
        foundation.update_ingestion_queue.assert_called_once_with(7, 3, "pending", NOW)
        assert foundation.create_ingestion_queue.call_count == 0

    def test_should_keep_existing_status_when_incrementing(self, service, foundation):
        foundation.list_ingestion_queue.return_value = [make_row(count=3, status="dismissed")]

        service.record_weak_verdict("ser-vs-estar", NOW)

        foundation.update_ingestion_queue.assert_called_once_with(1, 4, "dismissed", NOW)

    def test_should_propagate_foundation_exception_unchanged(self, service, foundation):
        boom = IngestionQueueValidationException(inner_exception=Exception("x"))
        foundation.list_ingestion_queue.side_effect = boom

        with pytest.raises(IngestionQueueValidationException) as info:
            service.record_weak_verdict("ser-vs-estar", NOW)
        assert info.value is boom


class TestListPending:
    def test_should_return_only_pending_rows_at_or_above_threshold_most_flagged_first(self, service, foundation):
        foundation.list_ingestion_queue.return_value = [
            make_row("a-below", count=2),
            make_row("b-at", count=3, row_id=2),
            make_row("c-most", count=5, row_id=3),
            make_row("d-done", count=9, status="ingested", row_id=4),
            make_row("e-dismissed", count=9, status="dismissed", row_id=5),
        ]

        actual = service.list_pending(3)

        assert [r.topic for r in actual] == ["c-most", "b-at"]
        foundation.list_ingestion_queue.assert_called_once_with()

    def test_should_return_empty_when_nothing_queued(self, service, foundation):
        foundation.list_ingestion_queue.return_value = []
        assert service.list_pending(3) == []


class TestMarkIngested:
    def test_should_set_status_ingested_and_keep_count_and_last_flagged(self, service, foundation):
        foundation.list_ingestion_queue.return_value = [make_row(count=4, row_id=7)]
        foundation.update_ingestion_queue.return_value = make_row(count=4, status="ingested", row_id=7)

        actual = service.mark_ingested("ser-vs-estar")

        assert actual.status == "ingested"
        foundation.update_ingestion_queue.assert_called_once_with(7, 4, "ingested", FIRST)

    def test_should_raise_not_found_when_topic_has_no_row(self, service, foundation):
        foundation.list_ingestion_queue.return_value = []

        with pytest.raises(IngestionQueueValidationException) as info:
            service.mark_ingested("ser-vs-estar")
        assert isinstance(info.value.inner_exception, NotFoundIngestionQueueException)
        assert foundation.update_ingestion_queue.call_count == 0
