"""Domain model + SQLAlchemy mapping for a recurring grammar-error pattern.

One row per (profile_id, category) pair — a learner's recurring mistake in a
grammar category (`ser vs estar`, `gender agreement`, ...). The
find-or-create/increment logic (`record_occurrence`) is Processing-tier, not
here — this broker's CRUD is pure select/insert/update, same shape as
`api/models/foundations/learner_profile/learner_profile.py`.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from api.models.base import Base


class MistakePatternRecord(Base):
    """SQLAlchemy ORM mapping for the `mistake_pattern` table."""

    __tablename__ = "mistake_pattern"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("learner_profile.id"), nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    occurrence_count: Mapped[int] = mapped_column(Integer, server_default="1", nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    status: Mapped[str] = mapped_column(String, server_default="active", nullable=False)


@dataclass
class MistakePattern:
    """Plain data-carrier used across broker/service/controller boundaries."""

    id: int
    profile_id: int
    category: str
    occurrence_count: int
    last_seen_at: datetime
    status: str
