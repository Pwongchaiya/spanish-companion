"""Re-exports the concrete FlagService class, declared directly in
flag_service.py (which inherits the Exceptions mixin by name) -- no
composition step here, matching LearnerProfileService/MistakePatternService's
rebuilt one-class-declared-once shape.
"""

from api.services.foundations.flag.flag_service import FlagService
from api.services.foundations.flag.i_flag_service import IFlagService

__all__ = [
    "IFlagService",
    "FlagService",
]
