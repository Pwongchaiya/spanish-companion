"""Domain model for the speaking-hours meter (roadmap item C1).

Computed on demand by ProgressOrchestrationService.get_speaking_total()
from `session_log` rows -- never persisted, same "read-only, computed from
other entities' rows" shape as TopicCoverageEntry and SessionScenario.

Seconds, not hours: the caller formats. The meter's milestone markers
("10 hours spoken") are presentation, so they live in ProgressView.tsx --
putting a milestone ladder here would bake a display choice into a
service.
"""

from dataclasses import dataclass


@dataclass
class SpeakingTotal:
    """Plain data-carrier returned by get_speaking_total().

    `session_count` counts only *completed* sessions -- the same rows that
    contributed to `total_seconds`. A session that's still running, or one
    whose process was killed before it could write `ended_at`, is in
    neither number.
    """

    total_seconds: float
    session_count: int
