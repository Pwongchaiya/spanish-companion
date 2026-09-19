"""Foundation service for the session_log_entry entity (roadmap C1/C3).

Wraps ISessionLogEntryBroker (api/brokers/session_log_entry/) with input
validation only -- pure CRUD, no duration maths, no streak counting. Both
aggregates are Orchestration-tier logic in
api/services/orchestrations/progress/progress_service.py.

Single broker dependency -> Foundation layer, not Orchestration, per
CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers. No Processing tier
either: completing a row is a plain field write against a known id, not
higher-order upsert/status-transition logic, so the Processing row's
2026-09-10 reversal does not pull anything out of here.

Split into a base logic file plus Validations/Exceptions mixins (this file,
session_log_entry_service_validations.py,
session_log_entry_service_exceptions.py) -- mirrors C#'s `partial class`
merging UserProfileService.cs / .Validations.cs / .Exceptions.cs into one
class, via the TopicCoveredService precedent. The concrete class is
declared directly in THIS file, inheriting the other two mixins by name --
no separate "_Base" intermediate class, no composition step in __init__.py.

Public methods are the ONLY thing that wraps with `_try_catch` (defined in
the Exceptions mixin) -- mirrors UserProfileService.cs's actual shape
(NL.Core.Users, Services/Foundations/UserProfiles/UserProfileService.cs:
31-66): each public method's entire body -- validate, then call the broker
-- is an inline nested closure passed straight to `_try_catch`, not a
separate `_do_thing` private method. complete_session_log_entry()'s
None-check is not exception handling: it is a business check on a normal
return value, the same shape as UserProfileService.cs:42-53's
ValidateUserProfileExists check on SelectUserProfileByIdAsync's result.
"""

from datetime import datetime
from typing import Optional

from api.brokers.logging import LoggingBroker
from api.brokers.session_log_entry.i_session_log_entry_broker import ISessionLogEntryBroker
from api.models.foundations.session_log_entry.exceptions import NotFoundSessionLogEntryException
from api.models.foundations.session_log_entry.session_log_entry import SessionLogEntry
from api.services.foundations.session_log_entry.i_session_log_entry_service import ISessionLogEntryService
from api.services.foundations.session_log_entry.session_log_entry_service_exceptions import (
    SessionLogEntryServiceExceptions,
)
from api.services.foundations.session_log_entry.session_log_entry_service_validations import (
    SessionLogEntryServiceValidations,
)


class SessionLogEntryService(
    SessionLogEntryServiceExceptions,
    SessionLogEntryServiceValidations,
    ISessionLogEntryService,
):
    """Owns SessionLogEntry CRUD. Validation checks are named methods
    (defined in the Validations mixin) rather than inlined.
    """

    def __init__(
        self,
        session_log_entry_broker: ISessionLogEntryBroker,
        *,
        logging_broker: LoggingBroker,
    ) -> None:
        self._session_log_entry_broker = session_log_entry_broker
        self._logging_broker = logging_broker

    def create_session_log_entry(self, started_at: datetime, scenario_slug: Optional[str] = None) -> SessionLogEntry:
        def action() -> SessionLogEntry:
            self._validate_session_log_entry_on_create(started_at)
            return self._session_log_entry_broker.insert_session_log_entry(started_at, scenario_slug)

        return self._try_catch(action)

    def list_session_log_entries(self) -> list[SessionLogEntry]:
        def action() -> list[SessionLogEntry]:
            return self._session_log_entry_broker.select_all_session_log_entries()

        return self._try_catch(action)

    def complete_session_log_entry(self, entry_id: int, ended_at: datetime, flag_count: int) -> SessionLogEntry:
        def action() -> SessionLogEntry:
            self._validate_session_log_entry_on_complete(entry_id, ended_at, flag_count)
            maybe_entry = self._session_log_entry_broker.update_session_log_entry(entry_id, ended_at, flag_count)
            if maybe_entry is None:
                raise NotFoundSessionLogEntryException()
            return maybe_entry

        return self._try_catch(action)

    def set_task_outcome(self, entry_id: int, task_outcome: str) -> SessionLogEntry:
        def action() -> SessionLogEntry:
            self._validate_session_log_entry_on_set_task_outcome(entry_id, task_outcome)
            maybe_entry = self._session_log_entry_broker.update_session_log_entry_task_outcome(entry_id, task_outcome)
            if maybe_entry is None:
                raise NotFoundSessionLogEntryException()
            return maybe_entry

        return self._try_catch(action)
