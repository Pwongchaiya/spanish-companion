"""Broker interface for `mistake_pattern` persistence.

`typing.Protocol`, not `ABC` — per CLAUDE.md's Broker-interfaces waiver
(matches `NL.Core.Entitlements`'s pattern of interfaces co-located with
their implementation). Pure CRUD only — no upsert, no find-by-category
increment logic. `record_occurrence()` (find-by-category -> insert or
increment) is Processing-tier logic, built later against this interface.
"""

from typing import Protocol

from api.models.foundations.mistake_pattern.mistake_pattern import MistakePattern


class IMistakePatternBroker(Protocol):
    """External-resource boundary for `mistake_pattern` persistence. Raw
    SQLAlchemy CRUD only — no business logic, no exception handling."""

    def select_by_profile(self, profile_id: int) -> list[MistakePattern]:
        """All mistake-pattern rows for the given profile."""
        ...

    def insert(self, profile_id: int, category: str) -> MistakePattern:
        """Insert a new mistake-pattern row. Caller (Processing) is
        responsible for only ever calling this when no row exists yet for
        (profile_id, category) — the DB unique constraint is the backstop."""
        ...

    def update(self, pattern_id: int, occurrence_count: int, status: str) -> MistakePattern:
        """Update the given row's occurrence_count and status. Raises
        whatever SQLAlchemy raises if pattern_id doesn't exist — Foundation
        maps that per the exception-hierarchy skill."""
        ...
