"""Processing service for ingestion_queue (roadmap F2).

Higher-order logic on top of the single Foundation dependency
(IIngestionQueueService): find-by-topic (over list_ingestion_queue's results)
composed with create-or-update. Foundation stays pure CRUD; the clock is a
caller-supplied `now`, so this tier never reads live time.

Same do-or-delegate shape as TopicCoveredProcessingService: no base/
validations/exceptions mixin split, Foundation exceptions propagate unchanged.
"""

from datetime import datetime

from api.models.foundations.ingestion_queue.exceptions import (
    IngestionQueueValidationException,
    NotFoundIngestionQueueException,
)
from api.models.foundations.ingestion_queue.ingestion_queue import IngestionQueue
from api.services.foundations.ingestion_queue.i_ingestion_queue_service import IIngestionQueueService


class IngestionQueueProcessingService:
    """Find-by-topic over Foundation's list_ingestion_queue(), then delegates
    to create_ingestion_queue/update_ingestion_queue.
    """

    def __init__(self, ingestion_queue_service: IIngestionQueueService) -> None:
        self._ingestion_queue_service = ingestion_queue_service

    def record_weak_verdict(self, topic: str, now: datetime) -> IngestionQueue:
        existing = self._find_by_topic(topic)
        if existing is None:
            return self._ingestion_queue_service.create_ingestion_queue(topic, 1, now)
        return self._ingestion_queue_service.update_ingestion_queue(
            existing.id, existing.weak_verdict_count + 1, existing.status, now
        )

    def list_pending(self, threshold: int) -> list[IngestionQueue]:
        rows = self._ingestion_queue_service.list_ingestion_queue()
        pending = [r for r in rows if r.status == "pending" and r.weak_verdict_count >= threshold]
        return sorted(pending, key=lambda r: (-r.weak_verdict_count, r.topic))

    def mark_ingested(self, topic: str) -> IngestionQueue:
        existing = self._find_by_topic(topic)
        if existing is None:
            raise IngestionQueueValidationException(inner_exception=NotFoundIngestionQueueException())
        return self._ingestion_queue_service.update_ingestion_queue(
            existing.id, existing.weak_verdict_count, "ingested", existing.last_flagged_at
        )

    def _find_by_topic(self, topic: str) -> IngestionQueue | None:
        rows = self._ingestion_queue_service.list_ingestion_queue()
        return next((row for row in rows if row.topic == topic), None)
