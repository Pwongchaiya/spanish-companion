"""Domain model + SQLAlchemy mapping for `ingestion_queue`.

Roadmap F2 (judge-driven ingestion queue). One row per RAE topic (a key of
`rag/data/topics.py` `TOPICS`) whose grounded explanations keep coming back
weak. `weak_verdict_count` is bumped by Processing's `record_weak_verdict`; a
topic is actionable once the count reaches INGESTION_QUEUE_THRESHOLD. No FK to
flags or the learner profile -- the queue is about corpus health, not a user.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from api.models.base import Base


class IngestionQueueRecord(Base):
    """SQLAlchemy ORM mapping for the `ingestion_queue` table."""

    __tablename__ = "ingestion_queue"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic: Mapped[str] = mapped_column(String(), unique=True, nullable=False)
    weak_verdict_count: Mapped[int] = mapped_column(Integer(), default=0, server_default="0", nullable=False)
    status: Mapped[str] = mapped_column(String(), default="pending", server_default="pending", nullable=False)
    first_flagged_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now(), nullable=False)
    last_flagged_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now(), nullable=False)


@dataclass
class IngestionQueue:
    """Plain data-carrier used across broker/service boundaries."""

    id: int
    topic: str
    weak_verdict_count: int
    status: str
    first_flagged_at: datetime
    last_flagged_at: datetime
