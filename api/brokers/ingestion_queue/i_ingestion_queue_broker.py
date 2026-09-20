"""Broker interface for `ingestion_queue` persistence.

`typing.Protocol`, not `ABC` -- per CLAUDE.md's Broker-interfaces waiver.
Pure CRUD only -- no find-by-topic, no upsert. `record_weak_verdict()`
(find-or-insert-or-increment) is Processing-tier logic, built against this
interface in ingestion_queue_processing_service.py.
"""

from datetime import datetime
from typing import Optional, Protocol

from api.models.foundations.ingestion_queue.ingestion_queue import IngestionQueue


class IIngestionQueueBroker(Protocol):
    """External-resource boundary for `ingestion_queue` persistence. Raw
    SQLAlchemy CRUD only -- no business logic, no exception handling."""

    def select_all_ingestion_queue(self) -> list[IngestionQueue]:
        """Every ingestion_queue row."""
        ...

    def insert_ingestion_queue(self, topic: str, weak_verdict_count: int, flagged_at: datetime) -> IngestionQueue:
        """Insert a new row (status pending, first/last_flagged_at = flagged_at).
        Caller (Processing) only calls this when no row exists for topic --
        the UNIQUE constraint is the backstop and lets
        sqlalchemy.exc.IntegrityError propagate unmodified."""
        ...

    def update_ingestion_queue(
        self, queue_id: int, weak_verdict_count: int, status: str, last_flagged_at: datetime
    ) -> Optional[IngestionQueue]:
        """Overwrite count/status/last_flagged_at. Returns None if queue_id
        doesn't exist -- Foundation maps that to NotFoundIngestionQueueException."""
        ...
