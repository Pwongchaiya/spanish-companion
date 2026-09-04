"""Interface for the turn-state Foundation service.

typing.Protocol, not abc.ABC, per this project's broker/service-interface
waiver (CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers table).
"""

from typing import Protocol


class ITurnStateService(Protocol):
    """External-facing contract for the turn-state Foundation service,
    feeding /api/events' listening/thinking/speaking indicator."""

    def set(self, state: str) -> None:
        """Record the pipeline's current turn state."""
        ...
