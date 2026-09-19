"""Domain model + SQLAlchemy mapping for the `session_log` table.

One row per voice-conversation session: when it started, when it ended, and
how many error flags it produced. Backs roadmap C1 (speaking-hours meter)
and C3 (longest unflagged stretch).

**Naming, deliberately not `SessionLog`:** `api/brokers/session_log/`
already holds `SessionLogBroker`/`FileSessionLogBroker` -- an unrelated
*file* broker that writes the end-of-session `.log` transcript plus the
live-transcript/turn-state files, fronted by `SessionLogService`
(`api/services/foundations/session_log/`). That name is taken. This entity
is the database row, so it is `SessionLogEntry` throughout
(`SessionLogEntryRecord`, `ISessionLogEntryBroker`, `SessionLogEntryService`)
while `__tablename__` stays `session_log`, the name the user signed off on.

`ended_at` is Optional: the row is inserted when the pipeline starts and
completed when it stops, so an in-flight -- or killed -- session has no end
yet. `flag_count` stays 0 until completion for the same reason; both
aggregates skip rows with `ended_at is None` so a never-completed session
can't be mistaken for a zero-flag one.

Dataclass/Record split and field ordering mirror
api/models/foundations/topic_covered/topic_covered.py.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from api.models.base import Base


class SessionLogEntryRecord(Base):
    """SQLAlchemy ORM mapping for the `session_log` table."""

    __tablename__ = "session_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now(), nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(), nullable=True)
    flag_count: Mapped[int] = mapped_column(Integer(), server_default="0", nullable=False)
    # D4 (migration 0007): NULL scenario_slug = no roleplay scenario; NULL
    # task_outcome = not a task scenario or not yet judged ('success'|'fail').
    scenario_slug: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    task_outcome: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)


@dataclass
class SessionLogEntry:
    """Plain data-carrier used across broker/service/controller boundaries."""

    id: int
    started_at: datetime
    ended_at: Optional[datetime]
    flag_count: int
    scenario_slug: Optional[str] = None
    task_outcome: Optional[str] = None
