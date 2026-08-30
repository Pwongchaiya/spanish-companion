"""Generation feature's output type.

Explanation is what GenerationService.explain() returns to Review — the
final grounded, sourced text plus the chunk's source_url for display.

File name mirrors api/models/session_lifecycle/session_status.py's
convention: the dataclass gets its own file named after itself, re-exported
through the package's __init__.py, rather than living directly in
__init__.py.
"""

from dataclasses import dataclass


@dataclass
class Explanation:
    explanation: str
    source_url: str
