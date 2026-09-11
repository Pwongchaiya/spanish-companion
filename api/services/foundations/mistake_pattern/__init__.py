"""Re-exports the concrete MistakePatternService class, declared directly in
mistake_pattern_service.py (which inherits the Validations/Exceptions mixins
by name) -- no composition step here, matching CalendlyInviteeFoundationService's
one-class-declared-once shape.
"""

from api.services.foundations.mistake_pattern.i_mistake_pattern_service import IMistakePatternService
from api.services.foundations.mistake_pattern.mistake_pattern_service import MistakePatternService

__all__ = [
    "IMistakePatternService",
    "MistakePatternService",
]
