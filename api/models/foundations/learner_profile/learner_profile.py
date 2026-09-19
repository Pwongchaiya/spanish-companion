"""Domain model + SQLAlchemy mapping for the singleton learner profile row.

Single-user app — no `user_id`, no auth. Exactly one row exists, created on
first use; the get-or-create logic itself (`ensure_profile`) lives in the
Processing tier, not here (see
Projects/spanish-companion/entities/learner-profile.md). This broker's CRUD
is pure select/insert/update, same shape as `select_profile` returning
`None` when the singleton row doesn't exist yet.

`MistakePattern` and `TopicCovered` (separate entities, same wave) hold a
`profile_id` FK to this table's `id` — resolved here and passed *down* to
them as a plain int parameter; they never look the profile up themselves.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from api.models.base import Base


class LearnerProfileRecord(Base):
    """SQLAlchemy ORM mapping for the `learner_profile` table."""

    __tablename__ = "learner_profile"

    id: Mapped[int] = mapped_column(primary_key=True)
    proficiency_level: Mapped[str | None]
    # Roadmap A6: async, best-effort CEFR estimate from the voice-conversation
    # transcript, distinct from proficiency_level (self-reported/onboarding
    # value) -- same nullable-String shape, set independently.
    cefr_estimate: Mapped[str | None]
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(), server_default=func.now(), onupdate=func.now(), nullable=False
    )


@dataclass
class LearnerProfile:
    """Plain data-carrier used across broker/service/controller boundaries."""

    id: int
    proficiency_level: str | None
    updated_at: datetime
    cefr_estimate: str | None = None
