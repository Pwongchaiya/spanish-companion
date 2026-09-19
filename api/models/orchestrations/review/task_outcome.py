"""Domain model for a task-scenario session's judged outcome (roadmap D4).

Composed on demand by ReviewOrchestrationService.get_task_outcome(), never
persisted itself -- `outcome` mirrors session_log.task_outcome ('success' |
'fail'), None meaning the session could not be judged yet (no transcript, or
the LLM judge failed/was unparseable).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TaskOutcome:
    """Plain data-carrier returned by get_task_outcome()."""

    scenario_slug: str
    label: str
    success_condition: str
    outcome: Optional[str]
