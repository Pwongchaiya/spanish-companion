"""SqlAlchemyLearnerProfileBroker — SQLAlchemy-backed ILearnerProfileBroker.

Owns the engine and the ORM<->dataclass mapping. No business logic, no
exception handling: raw SQLAlchemy exceptions propagate to the caller
(Foundation maps them per the exception-hierarchy skill). Mirrors
`api/brokers/mistake_pattern/mistake_pattern_broker.py`'s shape (engine
owned per-instance, Session opened per call, pg8000 driver-scheme
normalization in __init__).

No embedded __main__ self-check here -- this project's test strategy has no
broker-level test tier (only Services/Controllers get tests; see
IMistakePatternBroker's sibling implementation, which carries none either).
"""

from typing import Optional

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from api.models.foundations.learner_profile.learner_profile import LearnerProfile, LearnerProfileRecord


def _to_dataclass(record: LearnerProfileRecord) -> LearnerProfile:
    return LearnerProfile(id=record.id, proficiency_level=record.proficiency_level, updated_at=record.updated_at)


class SqlAlchemyLearnerProfileBroker:
    """SQLAlchemy-backed implementation of ILearnerProfileBroker."""

    def __init__(self, connection_string: str):
        # pg8000 (the only driver in requirements.txt) needs an explicit
        # "+pg8000" scheme — same normalization as
        # api/brokers/mistake_pattern/mistake_pattern_broker.py and
        # alembic/env.py.
        if connection_string.startswith("postgresql://"):
            connection_string = connection_string.replace("postgresql://", "postgresql+pg8000://", 1)
        self._engine = create_engine(connection_string)

    def select_learner_profile(self) -> LearnerProfile | None:
        with Session(self._engine) as session:
            record = session.execute(select(LearnerProfileRecord)).scalars().first()
            return _to_dataclass(record) if record is not None else None

    def insert_learner_profile(self, proficiency_level: str | None) -> LearnerProfile:
        record = LearnerProfileRecord(proficiency_level=proficiency_level)
        with Session(self._engine) as session:
            session.add(record)
            session.commit()
            session.refresh(record)
            return _to_dataclass(record)

    def update_learner_profile(self, profile_id: int, proficiency_level: str | None) -> Optional[LearnerProfile]:
        with Session(self._engine) as session:
            record = session.get(LearnerProfileRecord, profile_id)
            if record is None:
                return None
            record.proficiency_level = proficiency_level
            session.commit()
            session.refresh(record)
            return _to_dataclass(record)
