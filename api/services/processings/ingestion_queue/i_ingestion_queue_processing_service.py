"""Interface for the ingestion-queue Processing service.

typing.Protocol, not abc.ABC -- same convention as the Foundation interface.
"""

from datetime import datetime
from typing import Protocol

from api.models.foundations.ingestion_queue.ingestion_queue import IngestionQueue


class IIngestionQueueProcessingService(Protocol):
    """External-facing contract for IngestionQueue's Processing service."""

    def record_weak_verdict(self, topic: str, now: datetime) -> IngestionQueue:
        """Find-or-create-or-increment for a topic.

        No row yet -> create with weak_verdict_count=1 and first/last_flagged_at=now.
        Row exists -> weak_verdict_count + 1, last_flagged_at=now, status untouched
        (an ingested/dismissed topic keeps its status). Any exception from
        Foundation propagates unchanged.
        """
        ...

    def list_pending(self, threshold: int) -> list[IngestionQueue]:
        """Rows with status 'pending' and weak_verdict_count >= threshold, most-flagged first."""
        ...

    def mark_ingested(self, topic: str) -> IngestionQueue:
        """Set status to 'ingested' for topic, leaving its count and last_flagged_at as-is.

        Raises IngestionQueueValidationException (wrapping
        NotFoundIngestionQueueException) if no row exists for topic.
        """
        ...
