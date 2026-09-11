"""Domain model + SQLAlchemy mapping for `topic_covered`.

One row per grammar topic/scenario the learner has been exposed to, keyed by
`profile_id` (FK -> learner_profile.id, resolved by the caller and passed in
as a plain int — this entity never looks the profile up itself). Unique
constraint on (profile_id, topic) makes the Processing-tier upsert
(`record_topic`) safe; that find-or-touch logic lives in Processing, not
here — see Projects/spanish-companion/entities/topic-covered.md.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from api.models.base import Base


class TopicCoveredRecord(Base):
    """SQLAlchemy ORM mapping for the `topic_covered` table."""

    __tablename__ = "topic_covered"
    __table_args__ = (UniqueConstraint("profile_id", "topic", name="uq_topic_covered_profile_topic"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("learner_profile.id"), nullable=False)
    topic: Mapped[str] = mapped_column(String(), nullable=False)
    first_covered_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now(), nullable=False)
    last_practiced_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now(), nullable=False)


@dataclass
class TopicCovered:
    """Plain data-carrier used across broker/service/controller boundaries."""

    id: int
    profile_id: int
    topic: str
    first_covered_at: datetime
    last_practiced_at: datetime
