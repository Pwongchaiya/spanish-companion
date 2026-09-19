"""Domain model for one point on the pronunciation trend line (roadmap Phase 4).

Computed on demand by ProgressOrchestrationService.list_pronunciation_trend()
from `pronunciation_result` rows -- never persisted, same read-only shape as
SpeakingTotal. `overall` is the row's pronunciation_score.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class PronunciationTrendPoint:
    created_at: datetime
    accuracy: float
    fluency: float
    overall: float
