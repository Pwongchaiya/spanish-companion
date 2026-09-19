"""Domain model for a judged practice attempt.

LearnerProfile Phase 2 (see decisions/dynamic-bot-behavior-and-learner-memory.md):
record_practice() now judges the attempt against the flag's correction, so
the caller needs both the durable attempt record and the verdict -- not just
the attempt. No SQLAlchemy mapping: composed on demand by
ReviewOrchestrationService.record_practice(), never persisted itself.

A2 (graded practice-attempt verdict): `grade` is the raw "again" | "hard" |
"good" | "easy" verdict from GenerationService.judge_practice_attempt();
`mastered` stays a plain bool (`grade in ("good", "easy")`, derived by
ReviewOrchestrationService.record_practice()) so every existing
`mastered`-based consumer is unaffected.
"""

from dataclasses import dataclass

from api.brokers.practice_log import PracticeAttempt


@dataclass
class PracticeResult:
    """Plain data-carrier returned by record_practice()."""

    attempt: PracticeAttempt
    mastered: bool
    grade: str
