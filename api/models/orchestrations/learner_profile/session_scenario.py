"""Domain model for a suggested next-session scenario.

Combines learner memory (proficiency level, recurring mistake categories,
topic coverage) and recent flag history into one plain data-carrier for
Voice Conversation to open a session with -- what proficiency level to speak
at, what grammar category to steer toward, and what topic is either overdue
for review or newest to introduce.

No SQLAlchemy mapping: this is never persisted, only computed on demand by
LearnerProfileOrchestrationService.suggest_session_scenario() from four
other entities' already-persisted rows.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SessionScenario:
    """Plain data-carrier returned by suggest_session_scenario()."""

    proficiency_level: str
    focus_category: Optional[str]  # highest-occurrence active MistakePattern.category, or None
    suggested_topic: Optional[str]  # focus_category if set, else the topic due for review, else None
    recent_mistake_categories: List[str] = field(default_factory=list)  # newest-first, deduped
