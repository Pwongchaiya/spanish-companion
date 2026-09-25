"""Domain model + SQLAlchemy mapping for the `pronunciation_result` table.

One row per scored pronunciation attempt (Phase 4 B5): the reference text the
learner read, the four Azure assessment scores (plus prosody, which Azure only
returns for some locales, hence nullable), and the per-word breakdown as JSON.
No audio is stored. No foreign key to learner_profile: single-user project,
same reasoning as session_log (alembic/versions/0003_create_session_log_table.py).

Dataclass/Record split mirrors api/models/foundations/session_log_entry/session_log_entry.py.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, Index, String, false, func
from sqlalchemy.orm import Mapped, mapped_column

from api.models.base import Base


class PronunciationResultRecord(Base):
    """SQLAlchemy ORM mapping for the `pronunciation_result` table."""

    __tablename__ = "pronunciation_result"
    __table_args__ = (Index("ix_pronunciation_result_created_at", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now(), nullable=False)
    reference_text: Mapped[str] = mapped_column(String(), nullable=False)
    accuracy_score: Mapped[float] = mapped_column(Float(), nullable=False)
    fluency_score: Mapped[float] = mapped_column(Float(), nullable=False)
    completeness_score: Mapped[float] = mapped_column(Float(), nullable=False)
    pronunciation_score: Mapped[float] = mapped_column(Float(), nullable=False)
    prosody_score: Mapped[Optional[float]] = mapped_column(Float(), nullable=True)
    words_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON(), nullable=False)
    locale: Mapped[str] = mapped_column(String(), server_default="es-ES", nullable=False)
    is_word_drill: Mapped[bool] = mapped_column(Boolean(), server_default=false(), nullable=False)


@dataclass
class PronunciationResult:
    """Plain data-carrier used across broker/service/controller boundaries.
    `id` is None until the row is inserted."""

    id: Optional[int]
    created_at: datetime
    reference_text: str
    accuracy_score: float
    fluency_score: float
    completeness_score: float
    pronunciation_score: float
    prosody_score: Optional[float]
    words_json: list[dict[str, Any]]
    locale: str
    is_word_drill: bool = False
