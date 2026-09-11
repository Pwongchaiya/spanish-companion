"""SqlAlchemyTopicCoveredBroker — SQLAlchemy-backed ITopicCoveredBroker.

Owns the engine and the ORM<->dataclass mapping. No business logic, no
exception handling: raw SQLAlchemy exceptions propagate to the caller
(Foundation maps them per the exception-hierarchy skill). Mirrors
`api/brokers/learner_profile/learner_profile_broker.py`'s
SqlAlchemy<Entity>Broker shape (engine owned per-instance, Session opened
per call, pg8000 driver-scheme normalization in __init__).
"""

from datetime import datetime, timezone

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
        # api/brokers/learner_profile/learner_profile_broker.py and
        # alembic/env.py, applied here since this is a second place the
        # running app builds its own engine.
        if connection_string.startswith("postgresql://"):
            connection_string = connection_string.replace("postgresql://", "postgresql+pg8000://", 1)
        self._engine = create_engine(connection_string)

    def select_by_profile(self, profile_id: int) -> list[TopicCovered]:
        with Session(self._engine) as session:
            records = session.execute(
                select(TopicCoveredRecord).where(TopicCoveredRecord.profile_id == profile_id)
            ).scalars().all()
            return [_to_dataclass(record) for record in records]

    def insert(self, profile_id: int, topic: str) -> TopicCovered:
        record = TopicCoveredRecord(profile_id=profile_id, topic=topic)
        with Session(self._engine) as session:
            session.add(record)
            session.commit()
            session.refresh(record)
            return _to_dataclass(record)

    def touch(self, topic_id: int) -> TopicCovered:
        with Session(self._engine) as session:
            record = session.get(TopicCoveredRecord, topic_id)
            record.last_practiced_at = datetime.now(timezone.utc)
            session.commit()
            session.refresh(record)
            return _to_dataclass(record)


if __name__ == "__main__":
    # ponytail: self-check for the ORM<->dataclass mapping (_to_dataclass)
    # and touch()'s timestamp bump — against an in-memory sqlite engine, not
    # a live Postgres (this project's test strategy has no broker-tier
    # tests, see CLAUDE.md / test-broker-skill).
    from api.models.base import Base
    from api.models.foundations.learner_profile.learner_profile import LearnerProfileRecord

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    # Seed a learner_profile row so the FK resolves.
    with Session(engine) as seed_session:
        profile = LearnerProfileRecord(proficiency_level="A2")
        seed_session.add(profile)
        seed_session.commit()
        profile_id = profile.id

    broker = SqlAlchemyTopicCoveredBroker.__new__(SqlAlchemyTopicCoveredBroker)
    broker._engine = engine

    assert broker.select_by_profile(profile_id) == []

    created = broker.insert(profile_id=profile_id, topic="preterite-vs-imperfect")
    assert created.id is not None
    assert created.profile_id == profile_id
    assert created.topic == "preterite-vs-imperfect"
    assert isinstance(created.first_covered_at, datetime)
    original_last_practiced = created.last_practiced_at

    fetched = broker.select_by_profile(profile_id)
    assert len(fetched) == 1 and fetched[0].id == created.id

    touched = broker.touch(created.id)
    assert touched.last_practiced_at >= original_last_practiced
    assert touched.first_covered_at == created.first_covered_at, "first_covered_at must not change on touch"

    print("topic_covered_broker self-check passed")
