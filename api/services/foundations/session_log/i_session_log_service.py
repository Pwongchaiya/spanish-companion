"""Interface for the end-of-session log Foundation service.

typing.Protocol, not abc.ABC, per this project's broker/service-interface
waiver (CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers table).
"""

from pathlib import Path
from typing import List, Optional, Protocol

from api.models.flag import Flag


class ISessionLogService(Protocol):
    """External-facing contract for the end-of-session log Foundation
    service."""

    def save(self, turns: List[str], flags: List[Flag]) -> Optional[Path]:
        """Write one session's already-flattened turns (plus any flags) to
        a new timestamped log file. Returns None, writing nothing, if
        `turns` is empty -- a session with no turns has nothing worth a
        log file for manual review.
        """
        ...
