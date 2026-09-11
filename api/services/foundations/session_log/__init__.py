"""Re-exports the concrete SessionLogService class, declared directly in
session_log_service.py -- no composition step here, matching
LearnerProfileService's rebuilt one-class-declared-once shape.
"""

from api.services.foundations.session_log.i_session_log_service import ISessionLogService
from api.services.foundations.session_log.session_log_service import SessionLogService

__all__ = [
    "ISessionLogService",
    "SessionLogService",
]
