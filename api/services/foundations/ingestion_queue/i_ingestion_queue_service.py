"""Interface for the ingestion-queue Foundation service.

typing.Protocol, not abc.ABC (same convention as ITopicCoveredService).
Pure CRUD only -- no upsert, no find-by-topic. record_weak_verdict()
(find-or-insert-or-increment) is Processing-tier logic, built against this
interface in ingestion_queue_processing_service.py.
"""

from datetime import datetime
from typing import Protocol

from api.models.foundations.ingestion_queue.ingestion_queue import IngestionQueue


class IIngestionQueueService(Protocol):
    """External-facing contract for IngestionQueue's Foundation service."""

    def list_ingestion_queue(self) -> list[IngestionQueue]:
        """Every ingestion_queue row.

        Raises IngestionQueueDependencyException (wrapping
        FailedIngestionQueueStorageException) if the broker call fails.
        Raises IngestionQueueServiceException for any other unexpected failure.
        """
        ...

    def create_ingestion_queue(self, topic: str, weak_verdict_count: int, flagged_at: datetime) -> IngestionQueue:
        """Insert a new pending row for topic.

        Caller (Processing) only calls this when no row for topic exists.

        Raises IngestionQueueValidationException (wrapping
        InvalidIngestionQueueException) if topic is blank/not a TOPICS key or
        weak_verdict_count is negative.
        Raises IngestionQueueDependencyValidationException (wrapping
        AlreadyExistsIngestionQueueException) if the UNIQUE(topic) constraint fires.
        Raises IngestionQueueDependencyException (wrapping
        FailedIngestionQueueStorageException) for any other broker failure.
        Raises IngestionQueueServiceException for any other unexpected failure.
        """
        ...

    def update_ingestion_queue(
        self, queue_id: int, weak_verdict_count: int, status: str, last_flagged_at: datetime
    ) -> IngestionQueue:
        """Overwrite count/status/last_flagged_at for queue_id.

        Raises IngestionQueueValidationException (wrapping
        InvalidIngestionQueueException) if queue_id is not a positive int,
        count is negative, or status is not pending|ingested|dismissed; or
        (wrapping NotFoundIngestionQueueException) if queue_id doesn't exist.
        Raises IngestionQueueDependencyException (wrapping
        FailedIngestionQueueStorageException) if the broker call fails.
        Raises IngestionQueueServiceException for any other unexpected failure.
        """
        ...
