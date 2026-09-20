"""SqlAlchemyPersonaBroker -- SQLAlchemy-backed IPersonaBroker.

Same shape as api/brokers/pronunciation_result/pronunciation_result_broker.py:
engine owned per-instance, Session opened per call, pg8000 scheme
normalization in __init__, module-level `_to_dataclass`. No business logic,
no exception handling.
"""

from typing import Optional

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from api.models.foundations.persona.persona import Persona, PersonaRecord


def _to_dataclass(record: PersonaRecord) -> Persona:
    return Persona(
        id=record.id,
        slug=record.slug,
        name=record.name,
        setting=record.setting,
        memory=record.memory,
        updated_at=record.updated_at,
    )


class SqlAlchemyPersonaBroker:
    """SQLAlchemy-backed implementation of IPersonaBroker."""

    def __init__(self, connection_string: str):
        if connection_string.startswith("postgresql://"):
            connection_string = connection_string.replace("postgresql://", "postgresql+pg8000://", 1)
        self._engine = create_engine(connection_string)

    def insert_persona(self, persona: Persona) -> Persona:
        record = PersonaRecord(
            slug=persona.slug,
            name=persona.name,
            setting=persona.setting,
            memory=persona.memory,
            updated_at=persona.updated_at,
        )
        with Session(self._engine) as session:
            session.add(record)
            session.commit()
            session.refresh(record)
            return _to_dataclass(record)

    def select_persona_by_id(self, persona_id: int) -> Optional[Persona]:
        with Session(self._engine) as session:
            record = session.get(PersonaRecord, persona_id)
            return None if record is None else _to_dataclass(record)

    def select_persona_by_slug(self, slug: str) -> Optional[Persona]:
        with Session(self._engine) as session:
            record = session.execute(select(PersonaRecord).where(PersonaRecord.slug == slug)).scalars().first()
            return None if record is None else _to_dataclass(record)

    def select_all_personas(self) -> list[Persona]:
        with Session(self._engine) as session:
            records = session.execute(select(PersonaRecord).order_by(PersonaRecord.id)).scalars().all()
            return [_to_dataclass(record) for record in records]

    def update_persona(self, persona: Persona) -> Optional[Persona]:
        with Session(self._engine) as session:
            record = session.get(PersonaRecord, persona.id)
            if record is None:
                return None
            record.slug = persona.slug
            record.name = persona.name
            record.setting = persona.setting
            record.memory = persona.memory
            record.updated_at = persona.updated_at
            session.commit()
            session.refresh(record)
            return _to_dataclass(record)

    def delete_persona(self, persona_id: int) -> Optional[Persona]:
        with Session(self._engine) as session:
            record = session.get(PersonaRecord, persona_id)
            if record is None:
                return None
            deleted = _to_dataclass(record)
            session.delete(record)
            session.commit()
            return deleted


if __name__ == "__main__":
    # ponytail: assert-based self-check against in-memory sqlite -- covers the
    # ORM<->dataclass mapping, nullable memory, None-on-missing, and the unique
    # slug constraint. No live Postgres; no broker test tier (MEMORY.md).
    from datetime import datetime

    from sqlalchemy.exc import IntegrityError

    from api.models.base import Base

    def _make(slug: str, memory: Optional[str] = None) -> Persona:
        return Persona(
            id=None, slug=slug, name="Lucia", setting="cafe", memory=memory, updated_at=datetime(2026, 1, 1, 10, 0, 0)
        )

    broker = SqlAlchemyPersonaBroker("sqlite://")
    Base.metadata.create_all(broker._engine, tables=[PersonaRecord.__table__])

    a = broker.insert_persona(_make("cafe"))
    b = broker.insert_persona(_make("market", memory="likes tea"))
    assert a.id is not None and a.memory is None and b.memory == "likes tea", (a, b)
    assert broker.select_persona_by_id(a.id) == a
    assert broker.select_persona_by_slug("market") == b
    assert broker.select_persona_by_id(999) is None and broker.select_persona_by_slug("nope") is None
    assert [p.id for p in broker.select_all_personas()] == [a.id, b.id]

    later = datetime(2026, 2, 1, 9, 0, 0)
    updated = broker.update_persona(Persona(a.id, "cafe", "Lucia", "cafe", "met twice", later))
    assert updated is not None and updated.memory == "met twice" and updated.updated_at == later, updated
    assert broker.update_persona(Persona(999, "x", "x", "x", None, later)) is None

    try:
        broker.insert_persona(_make("cafe"))
        raise AssertionError("duplicate slug should raise IntegrityError")
    except IntegrityError:
        pass

    assert broker.delete_persona(a.id) == updated
    assert broker.delete_persona(a.id) is None
    assert [p.id for p in broker.select_all_personas()] == [b.id]
    print("persona_broker self-check passed")
