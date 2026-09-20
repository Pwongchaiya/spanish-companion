"""SqlAlchemySessionAudioBroker -- SQLAlchemy-backed ISessionAudioBroker.

Same shape as api/brokers/persona/persona_broker.py: engine owned per-instance,
Session opened per call, pg8000 scheme normalization in __init__. No business
logic, no exception handling.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from api.models.foundations.session_audio.session_audio import SessionAudio, SessionAudioRecord


def _to_dataclass(record: SessionAudioRecord) -> SessionAudio:
    return SessionAudio(
        id=record.id,
        session_log_id=record.session_log_id,
        file_path=record.file_path,
        duration_seconds=record.duration_seconds,
        created_at=record.created_at,
    )


class SqlAlchemySessionAudioBroker:
    """SQLAlchemy-backed implementation of ISessionAudioBroker."""

    def __init__(self, connection_string: str):
        if connection_string.startswith("postgresql://"):
            connection_string = connection_string.replace("postgresql://", "postgresql+pg8000://", 1)
        self._engine = create_engine(connection_string)

    def insert_session_audio(self, session_audio: SessionAudio) -> SessionAudio:
        record = SessionAudioRecord(
            session_log_id=session_audio.session_log_id,
            file_path=session_audio.file_path,
            duration_seconds=session_audio.duration_seconds,
            created_at=session_audio.created_at,
        )
        with Session(self._engine) as session:
            session.add(record)
            session.commit()
            session.refresh(record)
            return _to_dataclass(record)

    def select_session_audio_by_session_log_id(self, session_log_id: int) -> Optional[SessionAudio]:
        with Session(self._engine) as session:
            record = (
                session.execute(
                    select(SessionAudioRecord)
                    .where(SessionAudioRecord.session_log_id == session_log_id)
                    .order_by(SessionAudioRecord.id.desc())
                )
                .scalars()
                .first()
            )
            return None if record is None else _to_dataclass(record)

    def select_latest_session_audio(self) -> Optional[SessionAudio]:
        with Session(self._engine) as session:
            record = (
                session.execute(select(SessionAudioRecord).order_by(SessionAudioRecord.id.desc()))
                .scalars()
                .first()
            )
            return None if record is None else _to_dataclass(record)

    def select_session_audio_older_than(self, cutoff: datetime) -> list[SessionAudio]:
        with Session(self._engine) as session:
            records = (
                session.execute(
                    select(SessionAudioRecord)
                    .where(SessionAudioRecord.created_at < cutoff)
                    .order_by(SessionAudioRecord.id)
                )
                .scalars()
                .all()
            )
            return [_to_dataclass(record) for record in records]

    def delete_session_audio(self, session_audio_id: int) -> Optional[SessionAudio]:
        with Session(self._engine) as session:
            record = session.get(SessionAudioRecord, session_audio_id)
            if record is None:
                return None
            deleted = _to_dataclass(record)
            session.delete(record)
            session.commit()
            return deleted


if __name__ == "__main__":
    # ponytail: assert-based self-check against in-memory sqlite -- covers the
    # ORM<->dataclass mapping, latest-per-session read, retention read and
    # delete. No live Postgres; no broker test tier (MEMORY.md).
    from api.models.base import Base
    from api.models.foundations.session_log_entry.session_log_entry import SessionLogEntryRecord

    broker = SqlAlchemySessionAudioBroker("sqlite://")
    Base.metadata.create_all(broker._engine, tables=[SessionLogEntryRecord.__table__, SessionAudioRecord.__table__])
    # sqlite doesn't enforce the FK, so no session_log table is needed here.

    def _make(session_log_id: int, day: int) -> SessionAudio:
        return SessionAudio(None, session_log_id, f"a{session_log_id}.wav", 12.5, datetime(2026, 1, day))

    a = broker.insert_session_audio(_make(1, 1))
    b = broker.insert_session_audio(_make(1, 5))
    c = broker.insert_session_audio(_make(2, 10))
    assert a.id is not None and a.duration_seconds == 12.5, a
    assert broker.select_session_audio_by_session_log_id(1) == b
    assert broker.select_session_audio_by_session_log_id(99) is None
    assert broker.select_latest_session_audio() == c
    assert [r.id for r in broker.select_session_audio_older_than(datetime(2026, 1, 6))] == [a.id, b.id]
    assert broker.select_session_audio_older_than(datetime(2026, 1, 1)) == []
    assert broker.delete_session_audio(c.id) == c and broker.delete_session_audio(c.id) is None
    assert broker.select_latest_session_audio() == b
    print("session_audio_broker self-check passed")
