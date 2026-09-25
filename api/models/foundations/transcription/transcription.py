"""Free-form transcription result (no reference text -- unbiased recognition).

Mirrors api/models/foundations/pronunciation_assessment/pronunciation_assessment.py's shape.
"""

from dataclasses import dataclass


@dataclass
class Transcription:
    text: str
    duration_seconds: float
