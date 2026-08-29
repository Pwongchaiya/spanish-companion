"""Generation feature's output type.

Explanation is what GenerationService.explain() returns to Review — the
final grounded, sourced text plus the chunk's source_url for display.
"""

from dataclasses import dataclass


@dataclass
class Explanation:
    explanation: str
    source_url: str
