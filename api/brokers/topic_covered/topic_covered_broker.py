"""SqlAlchemyTopicCoveredBroker — SQLAlchemy-backed ITopicCoveredBroker.

Owns the engine and the ORM<->dataclass mapping. No business logic, no
exception handling: raw SQLAlchemy exceptions propagate to the caller
(Foundation maps them per the exception-hierarchy skill). Mirrors
`api/brokers/mistake_pattern/mistake_pattern_broker.py`'s shape (engine
owned per-instance, Session opened per call, pg8000 driver-scheme
normalization in __init__).
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from api.models.foundations.topic_covered.topic_covered import TopicCovered, TopicCoveredRecord


def _to_dataclass(record: TopicCoveredRecord) -> TopicCovered:
    return TopicCovered(
        id=record.id,
        profile_id=record.profile_id,
        topic=record.topic,
        first_covered_at=record.first_covered_at,
        last_practiced_at=record.last_practiced_at,
    )


class SqlAlchemyTopicCoveredBroker:
    """SQLAlchemy-backed implementation of ITopicCoveredBroker."""

    def __init__(self, connection_string: str):
        # pg8000 (the only driver in requirements.txt) needs an explicit
        # "+pg8000" scheme — same normalization as
        # api/brokers/mistake_pattern/mistake_pattern_broker.py and
        # alembic/env.py.
        if connection_string.startswith("postgresql://"):
            connection_string = connection_string.replace("postgresql://", "postgresql+pg8000://", 1)
        self._engine = create_engine(connection_string)

    def select_topic_covered_by_profile(self, profile_id: int) -> list[TopicCovered]:
        with Session(self._engine) as session:
            records = (
                session.execute(select(TopicCoveredRecord).where(TopicCoveredRecord.profile_id == profile_id))
                .scalars()
                .all()
            )
            return [_to_dataclass(record) for record in records]

    def insert_topic_covered(self, profile_id: int, topic: str) -> TopicCovered:
        record = TopicCoveredRecord(profile_id=profile_id, topic=topic)
        with Session(self._engine) as session:
            session.add(record)
            session.commit()
            session.refresh(record)
            return _to_dataclass(record)

    def touch_topic_covered(self, topic_id: int) -> Optional[TopicCovered]:
        with Session(self._engine) as session:
            record = session.get(TopicCoveredRecord, topic_id)
            if record is None:
                return None
            record.last_practiced_at = datetime.now(timezone.utc)
            session.commit()
            session.refresh(record)
            return _to_dataclass(record)
