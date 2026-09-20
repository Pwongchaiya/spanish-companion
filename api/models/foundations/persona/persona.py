"""Domain model + SQLAlchemy mapping for the `persona` table.

One row per conversation persona: unique `slug`, display `name`, `setting`
(scene description), and a nullable free-text `memory` carried between
sessions. Static definitions live in api/data/ later; the row exists to hold
memory. No foreign key to learner_profile: single-user project, same
reasoning as session_log (alembic/versions/0003_create_session_log_table.py).

Dataclass/Record split mirrors api/models/foundations/pronunciation_result/pronunciation_result.py.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from api.models.base import Base


class PersonaRecord(Base):
    """SQLAlchemy ORM mapping for the `persona` table."""

    __tablename__ = "persona"
    __table_args__ = (UniqueConstraint("slug", name="uq_persona_slug"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(Text(), nullable=False)
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    setting: Mapped[str] = mapped_column(Text(), nullable=False)
    memory: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now(), nullable=False)


@dataclass
class Persona:
    """Plain data-carrier used across broker/service/controller boundaries.
    `id` is None until the row is inserted."""

    id: Optional[int]
    slug: str
    name: str
    setting: str
    memory: Optional[str]
    updated_at: datetime
