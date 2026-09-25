"""Generation feature's output type.

Explanation is what GenerationService.explain() returns to Review — the
final grounded, sourced text plus the chunk's source_url and source_excerpt
(the retrieved passage text itself) for display.

File name mirrors api/models/foundations/session_lifecycle/session_status.py's
convention: the dataclass gets its own file named after itself, re-exported
through the package's __init__.py, rather than living directly in
__init__.py.
"""

from dataclasses import dataclass

# Single source of truth for the "couldn't ground this" fallback text --
# GenerationService.explain() sets it on broker/judge failure; Review compares
# against it (via is_fallback below) for F4 second-opinion + weak-verdict
# recording. Was duplicated as a literal in both places; drift between the two
# would silently break both features.
FALLBACK_EXPLANATION = "I'm not certain on that one."


@dataclass
class Explanation:
    explanation: str
    source_url: str
    source_excerpt: str

    @property
    def is_fallback(self) -> bool:
        """True when `explanation` is the fixed fallback text -- not a
        dataclass field, so dataclasses.asdict() (api/exposers/review.py)
        excludes it and the HTTP JSON response is unchanged.
        """
        return self.explanation == FALLBACK_EXPLANATION
