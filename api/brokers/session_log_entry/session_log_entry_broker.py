"""SqlAlchemySessionLogEntryBroker -- SQLAlchemy-backed ISessionLogEntryBroker.

Owns the engine and the ORM<->dataclass mapping. No business logic, no
exception handling: raw SQLAlchemy exceptions propagate to the caller
(Foundation maps them per the exception-hierarchy skill). Mirrors
`api/brokers/topic_covered/topic_covered_broker.py`'s shape exactly (engine
owned per-instance, Session opened per call, pg8000 driver-scheme
normalization in __init__, module-level `_to_dataclass` helper).
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from api.models.foundations.session_log_entry.session_log_entry import (
    SessionLogEntry,
    SessionLogEntryRecord,
)


def _to_dataclass(record: SessionLogEntryRecord) -> SessionLogEntry:
    return SessionLogEntry(
        id=record.id,
        started_at=record.started_at,
        ended_at=record.ended_at,
        flag_count=record.flag_count,
    )


class SqlAlchemySessionLogEntryBroker:
    """SQLAlchemy-backed implementation of ISessionLogEntryBroker."""

    def __init__(self, connection_string: str):
        # pg8000 (the only driver in requirements.txt) needs an explicit
        # "+pg8000" scheme -- same normalization as
        # api/brokers/topic_covered/topic_covered_broker.py and alembic/env.py.
        if connection_string.startswith("postgresql://"):
            connection_string = connection_string.replace("postgresql://", "postgresql+pg8000://", 1)
        self._engine = create_engine(connection_string)

    def insert_session_log_entry(self, started_at: datetime) -> SessionLogEntry:
        record = SessionLogEntryRecord(started_at=started_at, ended_at=None, flag_count=0)
        with Session(self._engine) as session:
            session.add(record)
            session.commit()
            session.refresh(record)
            return _to_dataclass(record)

    def select_all_session_log_entries(self) -> list[SessionLogEntry]:
        with Session(self._engine) as session:
            records = (
                session.execute(select(SessionLogEntryRecord).order_by(SessionLogEntryRecord.started_at))
                .scalars()
                .all()
            )
            return [_to_dataclass(record) for record in records]

    def update_session_log_entry(
        self, entry_id: int, ended_at: datetime, flag_count: int
    ) -> Optional[SessionLogEntry]:
        with Session(self._engine) as session:
            record = session.get(SessionLogEntryRecord, entry_id)
            if record is None:
                return None
            record.ended_at = ended_at
            record.flag_count = flag_count
            session.commit()
            session.refresh(record)
            return _to_dataclass(record)


if __name__ == "__main__":
    # ponytail: assert-based self-check against in-memory sqlite -- this
    # broker's only real logic is the ORM<->dataclass mapping, the
    # started_at ordering, and the None-on-missing-id return, all three of
    # which sqlite exercises identically to Postgres. No live Postgres, no
    # pytest (CLAUDE.md / MEMORY.md: this project has no broker test tier).
    from api.models.base import Base

    broker = SqlAlchemySessionLogEntryBroker("sqlite://")
    Base.metadata.create_all(broker._engine, tables=[SessionLogEntryRecord.__table__])

    second = broker.insert_session_log_entry(datetime(2026, 1, 2, 10, 0, 0))
    first = broker.insert_session_log_entry(datetime(2026, 1, 1, 10, 0, 0))
    assert second.ended_at is None and second.flag_count == 0, second

    # Inserted out of order on purpose: select_all must sort by started_at,
    # not by id -- C3's streak is only meaningful in start order.
    rows = broker.select_all_session_log_entries()
    assert [r.id for r in rows] == [first.id, second.id], rows

    completed = broker.update_session_log_entry(second.id, datetime(2026, 1, 2, 10, 30, 0), 3)
    assert completed is not None
    assert completed.ended_at == datetime(2026, 1, 2, 10, 30, 0) and completed.flag_count == 3, completed
    assert broker.update_session_log_entry(9999, datetime(2026, 1, 2, 11, 0, 0), 0) is None

    print("session_log_entry_broker self-check passed")
