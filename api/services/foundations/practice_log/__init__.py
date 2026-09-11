"""Re-exports the concrete PracticeLogService class, declared directly in
practice_log_service.py (which inherits the Validations/Exceptions mixins
by name) -- no composition step here, matching LearnerProfileService's
rebuilt one-class-declared-once shape.
"""

from api.services.foundations.practice_log.i_practice_log_service import IPracticeLogService
from api.services.foundations.practice_log.practice_log_service import PracticeLogService

__all__ = [
    "IPracticeLogService",
    "PracticeLogService",
]
