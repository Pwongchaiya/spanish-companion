"""Domain model for one row of the corpus coverage map (roadmap item F1).

Merges the RAG corpus's static topic list (rag/data/topics.py) with the
learner's own TopicCovered rows -- never persisted, computed on demand by
ProgressOrchestrationService.list_topic_coverage(), same "read-only,
computed from other entities' rows" shape as SessionScenario.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class TopicCoverageEntry:
    """Plain data-carrier returned by list_topic_coverage()."""

    topic: str
    covered: bool
    first_covered_at: Optional[datetime]
