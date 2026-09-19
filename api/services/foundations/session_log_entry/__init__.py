"""Re-exports the concrete SessionLogEntryService class, declared directly
in session_log_entry_service.py (which inherits the Validations/Exceptions
mixins by name) -- no composition step here, matching TopicCoveredService's
one-class-declared-once shape.
"""

from api.services.foundations.session_log_entry.i_session_log_entry_service import ISessionLogEntryService
from api.services.foundations.session_log_entry.session_log_entry_service import SessionLogEntryService

__all__ = [
    "ISessionLogEntryService",
    "SessionLogEntryService",
]
