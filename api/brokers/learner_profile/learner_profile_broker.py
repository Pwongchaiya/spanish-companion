"""SqlAlchemyLearnerProfileBroker — SQLAlchemy-backed ILearnerProfileBroker.

Owns the engine and the ORM<->dataclass mapping. No business logic, no
exception handling: raw SQLAlchemy exceptions propagate to the caller
(Foundation maps them per the exception-hierarchy skill). Mirrors
`rag/brokers/chunk_repository/chunk_repository_broker.py`'s
SqlAlchemy<Entity>RepositoryBroker shape (engine owned per-instance,
Session opened per call, pg8000 driver-scheme normalization in __init__).
"""

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
        # rag/brokers/chunk_repository/chunk_repository_broker.py and
        # alembic/env.py, applied here since this is a second place the
        # running app builds its own engine.
        if connection_string.startswith("postgresql://"):
            connection_string = connection_string.replace("postgresql://", "postgresql+pg8000://", 1)
        self._engine = create_engine(connection_string)

    def select_profile(self) -> LearnerProfile | None:
        with Session(self._engine) as session:
            record = session.execute(select(LearnerProfileRecord)).scalars().first()
            return _to_dataclass(record) if record is not None else None

    def insert_profile(self, proficiency_level: str | None) -> LearnerProfile:
        record = LearnerProfileRecord(proficiency_level=proficiency_level)
        with Session(self._engine) as session:
            session.add(record)
            session.commit()
            session.refresh(record)
            return _to_dataclass(record)

    def update_profile(self, profile_id: int, proficiency_level: str | None) -> LearnerProfile:
        with Session(self._engine) as session:
            record = session.get(LearnerProfileRecord, profile_id)
            record.proficiency_level = proficiency_level
            session.commit()
            session.refresh(record)
            return _to_dataclass(record)


if __name__ == "__main__":
    # ponytail: self-check for the ORM<->dataclass mapping (_to_dataclass),
    # the one piece of actual logic in this broker — against an in-memory
    # sqlite engine, not a live Postgres (this project's test strategy has
    # no broker-tier tests, see CLAUDE.md / test-broker-skill).
    from datetime import datetime, timezone

    from api.models.base import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    broker = SqlAlchemyLearnerProfileBroker.__new__(SqlAlchemyLearnerProfileBroker)
    broker._engine = engine

    assert broker.select_profile() is None, "expected no profile row before insert"

    created = broker.insert_profile(proficiency_level="A2")
    assert created.id is not None
    assert created.proficiency_level == "A2"
    assert isinstance(created.updated_at, datetime)

    fetched = broker.select_profile()
    assert fetched is not None and fetched.id == created.id and fetched.proficiency_level == "A2"

    updated = broker.update_profile(created.id, proficiency_level="B1")
    assert updated.proficiency_level == "B1"
    assert broker.select_profile().proficiency_level == "B1"

    print("learner_profile_broker self-check passed")
