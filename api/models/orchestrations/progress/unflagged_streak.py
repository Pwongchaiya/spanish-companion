"""Domain model for the longest-unflagged-stretch meter (roadmap item C3).

Computed on demand by
ProgressOrchestrationService.get_longest_unflagged_streak() from
`session_log` rows -- never persisted, same shape as SpeakingTotal.

"Unflagged" means a completed session whose `flag_count` is 0. A streak is
a run of those, consecutive in `started_at` order.
"""

from dataclasses import dataclass


@dataclass
class UnflaggedStreak:
    """Plain data-carrier returned by get_longest_unflagged_streak().

    `current` is the streak still running (the trailing run of zero-flag
    sessions); `longest` is the best ever. `current` is always <=
    `longest`, and both are 0 when no session has been completed yet.
    """

    longest: int
    current: int
