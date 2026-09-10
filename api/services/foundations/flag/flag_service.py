"""Foundation service for flagged-grammar-error persistence.

Wraps FlagBroker (api/brokers/flag/) with the lookup logic Review currently
does inline. list_flags() and _get_flag() moved here from ReviewOrchestrator
(api/services/orchestrations/review/review_service.py) -- same linear-scan
approach. list_flags() came over as an unwrapped pass-through and stayed one
until H7 of the architecture conformance audit; every public method here now
routes through _try_catch.

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
from api.brokers.logging import LoggingBroker
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
        *,
        logging_broker: LoggingBroker,
    ) -> None:
        self._flag_broker = flag_broker
        self._logging_broker = logging_broker

    def list_flags(self) -> List[Flag]:
        """The current flag list, for the UI's flagged-list -> selection step.

        Routed through _try_catch. FlagBroker.load_flags() already returns []
        for a missing or corrupt file, so "no flags yet" still comes back as
        [] rather than an exception -- but that only ever covered the empty
        case, and every other broker failure (unreadable file, permission
        error) escaped raw. H7 of the architecture conformance audit found
        that reaching Flask as an unmapped 500 through
        ReviewOrchestrator.list_flags(); the guard lives here because
        api/app.py's /api/events SSE stream calls this method directly too,
        bypassing the orchestrator entirely.
        """
        return self._try_catch(self._list_flags)

    def _list_flags(self) -> List[Flag]:
        try:
            return self._flag_broker.load_flags()
        except Exception as e:
            # Same wrapping as _get_flag/_save_flags below, for the same
            # reason: without it a broker failure lands in _try_catch's
            # generic Exception branch as FlagServiceException rather than
            # the FlagDependencyException i_flag_service.py promises.
            raise FlagUnavailableError(str(e)) from e

    def get_flag(self, flag_id: str) -> Flag:
        return self._try_catch(lambda: self._get_flag(flag_id))

    def _get_flag(self, flag_id: str) -> Flag:
        # ponytail: linear scan of a freshly loaded list on every call. MVP
        # scale is one conversation's flags (tens), and reloading each time is
        # the point -- Voice Conversation rewrites the file mid-session, so a
        # cached dict would go stale. Build an id->Flag index only if a single
        # request ever needs more than one lookup.
        try:
            flags = self._flag_broker.load_flags()
        except Exception as e:
            # Mirrors _save_flags's wrapping below -- without this, a broker
            # failure here would fall through _try_catch's generic Exception
            # branch as FlagServiceException, contradicting this class's own
            # get_flag() docstring (and i_flag_service.py's), which promises
            # FlagDependencyException for "the underlying FlagBroker call
            # fails".
            raise FlagUnavailableError(str(e)) from e
        for flag in flags:
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
