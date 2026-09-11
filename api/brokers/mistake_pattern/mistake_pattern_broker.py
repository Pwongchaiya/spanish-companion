"""SqlAlchemyMistakePatternBroker — SQLAlchemy-backed IMistakePatternBroker.

Owns the engine and the ORM<->dataclass mapping. No business logic, no
exception handling: raw SQLAlchemy exceptions propagate to the caller
(Foundation maps them per the exception-hierarchy skill). Mirrors
`api/brokers/learner_profile/learner_profile_broker.py`'s shape (engine
owned per-instance, Session opened per call, pg8000 driver-scheme
normalization in __init__).
"""

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

    def select_by_profile(self, profile_id: int) -> list[MistakePattern]:
        with Session(self._engine) as session:
            records = session.execute(
                select(MistakePatternRecord).where(MistakePatternRecord.profile_id == profile_id)
            ).scalars().all()
            return [_to_dataclass(record) for record in records]

    def insert(self, profile_id: int, category: str) -> MistakePattern:
        record = MistakePatternRecord(profile_id=profile_id, category=category)
        with Session(self._engine) as session:
            session.add(record)
            session.commit()
            session.refresh(record)
            return _to_dataclass(record)

    def update(self, pattern_id: int, occurrence_count: int, status: str) -> MistakePattern:
        with Session(self._engine) as session:
            record = session.get(MistakePatternRecord, pattern_id)
            record.occurrence_count = occurrence_count
            record.status = status
            session.commit()
            session.refresh(record)
            return _to_dataclass(record)


if __name__ == "__main__":
    # ponytail: self-check for the ORM<->dataclass mapping (_to_dataclass),
    # the one piece of actual logic in this broker — against an in-memory
    # sqlite engine, not a live Postgres (this project's test strategy has
    # no broker-tier tests, see CLAUDE.md / test-broker-skill).
    from datetime import datetime

    from api.models.base import Base
    from api.models.foundations.learner_profile.learner_profile import LearnerProfileRecord  # noqa: F401  (FK target)

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    # seed a learner_profile row so the FK is satisfiable
    with Session(engine) as session:
        profile = LearnerProfileRecord(proficiency_level="A2")
        session.add(profile)
        session.commit()
        profile_id = profile.id

    broker = SqlAlchemyMistakePatternBroker.__new__(SqlAlchemyMistakePatternBroker)
    broker._engine = engine

    assert broker.select_by_profile(profile_id) == [], "expected no rows before insert"

    created = broker.insert(profile_id=profile_id, category="ser vs estar")
    assert created.id is not None
    assert created.profile_id == profile_id
    assert created.category == "ser vs estar"
    assert created.occurrence_count == 1
    assert created.status == "active"
    assert isinstance(created.last_seen_at, datetime)

    fetched = broker.select_by_profile(profile_id)
    assert len(fetched) == 1 and fetched[0].id == created.id

    updated = broker.update(created.id, occurrence_count=3, status="resolved")
    assert updated.occurrence_count == 3
    assert updated.status == "resolved"
    assert broker.select_by_profile(profile_id)[0].occurrence_count == 3

    print("mistake_pattern_broker self-check passed")
