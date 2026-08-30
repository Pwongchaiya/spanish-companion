"""Foundation service for flagged-grammar-error persistence.

Wraps FlagBroker (api/brokers/flag/) with the lookup logic Review currently
does inline. list_flags() and _get_flag() move here VERBATIM from
ReviewOrchestrator (api/services/review/review_service.py) -- same
linear-scan approach, same reasoning for why list_flags() bypasses
_try_catch. Wave 5 (dispatched separately) rewires ReviewOrchestrator to
call this service instead of doing this itself; nothing calls this service
yet.

Single broker dependency -> Foundation layer, not Orchestration, per
CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers.

Split into a base logic file plus an Exceptions mixin (this file,
flag_service_exceptions.py), combined into the concrete FlagService in
__init__.py -- mirrors C#'s `partial class` merging multiple files into one
class (python-adaptations-skill.md's Architecture Patterns table), the same
multi-inheritance-merge already used for Session Lifecycle and Review in
this codebase.

No Validations mixin/file: get_flag()'s only failure mode is not-found,
which is validation-shaped via NotFoundFlagException itself -- there is no
separate rejected-input case to check before calling the broker. Matches
HybridRetrievalService's precedent (no validations file at all when there
is nothing to validate) rather than inventing an empty one.
"""

from typing import List

from api.brokers.flag import FlagBroker
from api.brokers.logging import LoggingBroker, StdlibLoggingBroker
from api.models.flag import Flag
from api.models.flag.exceptions import FlagUnavailableError, NotFoundFlagException


class _FlagServiceBase:
    """Owns Flag persistence + lookup.

    Public methods delegate to a private `_do_thing` method through
    `_try_catch` (defined in the Exceptions mixin), per python-adaptations-
    skill.md's TryCatch translation.
    """

    def __init__(
        self,
        flag_broker: FlagBroker,
        logging_broker: LoggingBroker = StdlibLoggingBroker(),
    ) -> None:
        self._flag_broker = flag_broker
        self._logging_broker = logging_broker

    def list_flags(self) -> List[Flag]:
        """The current flag list, for the UI's flagged-list -> selection step.

        Pass-through, deliberately NOT routed through _try_catch:
        FlagBroker.load_flags() already returns [] for a missing or corrupt
        file, and "no flags yet" is a normal state, not an error. Same
        treatment as ConversationSessionService.get_status() and
        ReviewOrchestrator.list_flags() (moved here verbatim), the same
        reasoning both already established.
        """
        return self._flag_broker.load_flags()

    def get_flag(self, flag_id: str) -> Flag:
        return self._try_catch(lambda: self._get_flag(flag_id))

    def _get_flag(self, flag_id: str) -> Flag:
        # ponytail: linear scan of a freshly loaded list on every call. MVP
        # scale is one conversation's flags (tens), and reloading each time is
        # the point -- Voice Conversation rewrites the file mid-session, so a
        # cached dict would go stale. Build an id->Flag index only if a single
        # request ever needs more than one lookup.
        for flag in self._flag_broker.load_flags():
            if flag.id == flag_id:
                return flag
        raise NotFoundFlagException(flag_id)

    def save_flags(self, flags: List[Flag]) -> None:
        self._try_catch(lambda: self._save_flags(flags))

    def _save_flags(self, flags: List[Flag]) -> None:
        try:
            self._flag_broker.save_flags(flags)
        except Exception as e:
            raise FlagUnavailableError(str(e)) from e
