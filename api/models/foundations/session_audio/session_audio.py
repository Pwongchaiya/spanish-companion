"""Domain model + SQLAlchemy mapping for the `session_audio` table (roadmap E3).

One row per recorded voice session: the local-disk WAV's path and duration.
Audio lives on disk (data/audio/), never in the DB. `session_log_id` is a real
FK to session_log.id -- the one deliberate exception to this project's
no-FK habit, because retention pruning and replay both key off the session.

Dataclass/Record split mirrors api/models/foundations/persona/persona.py.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from api.models.base import Base


class SessionAudioRecord(Base):
    """SQLAlchemy ORM mapping for the `session_audio` table."""

    __tablename__ = "session_audio"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_log_id: Mapped[int] = mapped_column(ForeignKey("session_log.id"), nullable=False)
    file_path: Mapped[str] = mapped_column(Text(), nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now(), nullable=False)


@dataclass
class SessionAudio:
    """Plain data-carrier used across broker/service/controller boundaries.
    `id` is None until the row is inserted."""

    id: Optional[int]
    session_log_id: int
    file_path: str
    duration_seconds: float
    created_at: datetime
