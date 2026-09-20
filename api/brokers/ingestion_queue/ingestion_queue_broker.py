"""SqlAlchemyIngestionQueueBroker -- SQLAlchemy-backed IIngestionQueueBroker.

Owns the engine and the ORM<->dataclass mapping. No business logic, no
exception handling: raw SQLAlchemy exceptions propagate to Foundation. Same
shape as `api/brokers/topic_covered/topic_covered_broker.py`.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from api.models.foundations.ingestion_queue.ingestion_queue import IngestionQueue, IngestionQueueRecord


def _to_dataclass(record: IngestionQueueRecord) -> IngestionQueue:
    return IngestionQueue(
        id=record.id,
        topic=record.topic,
        weak_verdict_count=record.weak_verdict_count,
        status=record.status,
        first_flagged_at=record.first_flagged_at,
        last_flagged_at=record.last_flagged_at,
    )


class SqlAlchemyIngestionQueueBroker:
    """SQLAlchemy-backed implementation of IIngestionQueueBroker."""

    def __init__(self, connection_string: str):
        # pg8000 needs an explicit "+pg8000" scheme -- same normalization as
        # api/brokers/topic_covered/topic_covered_broker.py and alembic/env.py.
        if connection_string.startswith("postgresql://"):
            connection_string = connection_string.replace("postgresql://", "postgresql+pg8000://", 1)
        self._engine = create_engine(connection_string)

    def select_all_ingestion_queue(self) -> list[IngestionQueue]:
        with Session(self._engine) as session:
            records = session.execute(select(IngestionQueueRecord)).scalars().all()
            return [_to_dataclass(record) for record in records]

    def insert_ingestion_queue(self, topic: str, weak_verdict_count: int, flagged_at: datetime) -> IngestionQueue:
        record = IngestionQueueRecord(
            topic=topic,
            weak_verdict_count=weak_verdict_count,
            status="pending",
            first_flagged_at=flagged_at,
            last_flagged_at=flagged_at,
        )
        with Session(self._engine) as session:
            session.add(record)
            session.commit()
            session.refresh(record)
            return _to_dataclass(record)

    def update_ingestion_queue(
        self, queue_id: int, weak_verdict_count: int, status: str, last_flagged_at: datetime
    ) -> Optional[IngestionQueue]:
        with Session(self._engine) as session:
            record = session.get(IngestionQueueRecord, queue_id)
            if record is None:
                return None
            record.weak_verdict_count = weak_verdict_count
            record.status = status
            record.last_flagged_at = last_flagged_at
            session.commit()
            session.refresh(record)
            return _to_dataclass(record)
