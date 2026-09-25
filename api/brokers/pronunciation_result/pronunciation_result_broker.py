"""SqlAlchemyPronunciationResultBroker -- SQLAlchemy-backed IPronunciationResultBroker.

Same shape as api/brokers/session_log_entry/session_log_entry_broker.py:
engine owned per-instance, Session opened per call, pg8000 scheme
normalization in __init__, module-level `_to_dataclass`. No business logic,
no exception handling.
"""

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from api.models.foundations.pronunciation_result.pronunciation_result import (
    PronunciationResult,
    PronunciationResultRecord,
)


def _to_dataclass(record: PronunciationResultRecord) -> PronunciationResult:
    return PronunciationResult(
        id=record.id,
        created_at=record.created_at,
        reference_text=record.reference_text,
        accuracy_score=record.accuracy_score,
        fluency_score=record.fluency_score,
        completeness_score=record.completeness_score,
        pronunciation_score=record.pronunciation_score,
        prosody_score=record.prosody_score,
        words_json=record.words_json,
        locale=record.locale,
        is_word_drill=record.is_word_drill,
    )


class SqlAlchemyPronunciationResultBroker:
    """SQLAlchemy-backed implementation of IPronunciationResultBroker."""

    def __init__(self, connection_string: str):
        if connection_string.startswith("postgresql://"):
            connection_string = connection_string.replace("postgresql://", "postgresql+pg8000://", 1)
        self._engine = create_engine(connection_string)

    def insert_pronunciation_result(self, result: PronunciationResult) -> PronunciationResult:
        record = PronunciationResultRecord(
            created_at=result.created_at,
            reference_text=result.reference_text,
            accuracy_score=result.accuracy_score,
            fluency_score=result.fluency_score,
            completeness_score=result.completeness_score,
            pronunciation_score=result.pronunciation_score,
            prosody_score=result.prosody_score,
            words_json=result.words_json,
            locale=result.locale,
            is_word_drill=result.is_word_drill,
        )
        with Session(self._engine) as session:
            session.add(record)
            session.commit()
            session.refresh(record)
            return _to_dataclass(record)

    def select_all_pronunciation_results(self) -> list[PronunciationResult]:
        with Session(self._engine) as session:
            records = (
                session.execute(select(PronunciationResultRecord).order_by(PronunciationResultRecord.created_at))
                .scalars()
                .all()
            )
            return [_to_dataclass(record) for record in records]


if __name__ == "__main__":
    # ponytail: assert-based self-check against in-memory sqlite -- covers the
    # ORM<->dataclass mapping (incl. JSON round-trip, nullable prosody) and
    # created_at ordering. No live Postgres; no broker test tier (MEMORY.md).
    from datetime import datetime

    from api.models.base import Base

    def _make(created_at: datetime, prosody: float | None, is_word_drill: bool = False) -> PronunciationResult:
        return PronunciationResult(
            id=None,
            created_at=created_at,
            reference_text="hola",
            accuracy_score=90.0,
            fluency_score=80.0,
            completeness_score=100.0,
            pronunciation_score=85.5,
            prosody_score=prosody,
            words_json=[{"word": "hola", "accuracy": 90.0}],
            locale="es-ES",
            is_word_drill=is_word_drill,
        )

    broker = SqlAlchemyPronunciationResultBroker("sqlite://")
    Base.metadata.create_all(broker._engine, tables=[PronunciationResultRecord.__table__])

    newer = broker.insert_pronunciation_result(_make(datetime(2026, 1, 2, 10, 0, 0), None))
    older = broker.insert_pronunciation_result(_make(datetime(2026, 1, 1, 10, 0, 0), 70.0, True))
    assert newer.id is not None and newer.prosody_score is None, newer
    assert newer.words_json == [{"word": "hola", "accuracy": 90.0}], newer

    rows = broker.select_all_pronunciation_results()
    assert [r.id for r in rows] == [older.id, newer.id], rows
    assert rows[0].prosody_score == 70.0 and rows[0].locale == "es-ES", rows[0]
    assert rows[0].is_word_drill is True and rows[1].is_word_drill is False, rows
