"""Broker interface for `pronunciation_result` persistence (Phase 4 B5).

`typing.Protocol`, not `ABC`, per CLAUDE.md's Broker-interfaces waiver. Pure
CRUD only -- no trend/average logic; that is higher-tier work built against
this interface. Mirrors api/brokers/session_log_entry/i_session_log_entry_broker.py.
"""

from typing import Protocol

from api.models.foundations.pronunciation_result.pronunciation_result import PronunciationResult


class IPronunciationResultBroker(Protocol):
    """External-resource boundary for `pronunciation_result` persistence. Raw
    SQLAlchemy CRUD only -- no business logic, no exception handling."""

    def insert_pronunciation_result(self, result: PronunciationResult) -> PronunciationResult:
        """Insert one row from `result` (its `id` is ignored) and return it
        with the assigned id and stored created_at."""
        ...

    def select_all_pronunciation_results(self) -> list[PronunciationResult]:
        """Every row, ordered by `created_at` ascending (oldest first)."""
        ...
