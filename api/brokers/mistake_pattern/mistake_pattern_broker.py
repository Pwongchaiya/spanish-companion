"""SqlAlchemyMistakePatternBroker — SQLAlchemy-backed IMistakePatternBroker.

Owns the engine and the ORM<->dataclass mapping. No business logic, no
exception handling: raw SQLAlchemy exceptions propagate to the caller
(Foundation maps them per the exception-hierarchy skill). Mirrors
`api/brokers/learner_profile/learner_profile_broker.py`'s shape (engine
owned per-instance, Session opened per call, pg8000 driver-scheme
normalization in __init__).
"""

from typing import Optional

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from api.models.foundations.mistake_pattern.mistake_pattern import MistakePattern, MistakePatternRecord


def _to_dataclass(record: MistakePatternRecord) -> MistakePattern:
    return MistakePattern(
        id=record.id,
        profile_id=record.profile_id,
        category=record.category,
        occurrence_count=record.occurrence_count,
        last_seen_at=record.last_seen_at,
        status=record.status,
    )


class SqlAlchemyMistakePatternBroker:
    """SQLAlchemy-backed implementation of IMistakePatternBroker."""

    def __init__(self, connection_string: str):
        # pg8000 (the only driver in requirements.txt) needs an explicit
        # "+pg8000" scheme — same normalization as
        # api/brokers/learner_profile/learner_profile_broker.py and
        # alembic/env.py.
        if connection_string.startswith("postgresql://"):
            connection_string = connection_string.replace("postgresql://", "postgresql+pg8000://", 1)
        self._engine = create_engine(connection_string)

    def select_mistake_patterns_by_profile(self, profile_id: int) -> list[MistakePattern]:
        with Session(self._engine) as session:
            records = session.execute(
                select(MistakePatternRecord).where(MistakePatternRecord.profile_id == profile_id)
            ).scalars().all()
            return [_to_dataclass(record) for record in records]

    def insert_mistake_pattern(self, profile_id: int, category: str) -> MistakePattern:
        record = MistakePatternRecord(profile_id=profile_id, category=category)
        with Session(self._engine) as session:
            session.add(record)
            session.commit()
            session.refresh(record)
            return _to_dataclass(record)

    def update_mistake_pattern(
        self, pattern_id: int, occurrence_count: int, status: str
    ) -> Optional[MistakePattern]:
        with Session(self._engine) as session:
            record = session.get(MistakePatternRecord, pattern_id)
            if record is None:
                return None
            record.occurrence_count = occurrence_count
            record.status = status
            session.commit()
            session.refresh(record)
            return _to_dataclass(record)
