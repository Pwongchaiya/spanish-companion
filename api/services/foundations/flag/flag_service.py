"""Foundation service for flagged-grammar-error persistence.

Wraps FlagBroker (api/brokers/flag/) with the lookup logic Review currently
does inline. list_flags() and _get_flag() moved here from ReviewOrchestrationService
(api/services/orchestrations/review/review_service.py) -- same linear-scan
approach. list_flags() came over as an unwrapped pass-through and stayed one
until H7 of the architecture conformance audit; every public method here now
routes through _try_catch.

Single broker dependency -> Foundation layer, not Orchestration, per
CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers.

One class, declared once here, `class FlagService(FlagServiceExceptions,
IFlagService):` -- constructor and public methods directly on it. No
separate `_FlagServiceBase` + __init__.py composition step (that was the
invented-`_ServiceBase` pattern CLAUDE.md explicitly disallows -- removed,
matches LearnerProfileService/MistakePatternService's rebuilt shape).

Public methods are the ONLY thing that wraps with `_try_catch` (defined in
the Exceptions mixin): each public method's entire body is an inline nested
closure passed straight to `_try_catch`, not a separate `_do_thing` private
method with its own try/except. No local try/except inside the closures --
every exception (domain leaf, raw exception, or otherwise) propagates
untouched to `_try_catch`, the single dispatch point that classifies and
wraps. The previous per-method wrapping of broker failures into
FlagUnavailableError is preserved, just moved into the closure itself.

No Validations mixin/file: get_flag()'s only failure mode is not-found,
which is validation-shaped via NotFoundFlagException itself -- there is no
separate rejected-input case to check before calling the broker. Matches
HybridRetrievalOrchestrationService's precedent (no validations file at all when there
is nothing to validate) rather than inventing an empty one.
"""

from typing import List

from api.brokers.flag import FlagBroker
from api.brokers.logging import LoggingBroker
from api.models.foundations.flag import Flag
from api.models.foundations.flag.exceptions import FlagUnavailableError, NotFoundFlagException
from api.services.foundations.flag.flag_service_exceptions import FlagServiceExceptions
from api.services.foundations.flag.i_flag_service import IFlagService


class FlagService(FlagServiceExceptions, IFlagService):
    """Owns Flag persistence + lookup."""

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
        ReviewOrchestrationService.list_flags(); the guard lives here because
        api/app.py's /api/events SSE stream calls this method directly too,
        bypassing the orchestrator entirely.
        """

        def action() -> List[Flag]:
            try:
                return self._flag_broker.load_flags()
            except Exception as e:
                raise FlagUnavailableError(str(e)) from e

        return self._try_catch(action)

    def get_flag(self, flag_id: str) -> Flag:
        # ponytail: linear scan of a freshly loaded list on every call. MVP
        # scale is one conversation's flags (tens), and reloading each time is
        # the point -- Voice Conversation rewrites the file mid-session, so a
        # cached dict would go stale. Build an id->Flag index only if a single
        # request ever needs more than one lookup.
        def action() -> Flag:
            try:
                flags = self._flag_broker.load_flags()
            except Exception as e:
                raise FlagUnavailableError(str(e)) from e
            for flag in flags:
                if flag.id == flag_id:
                    return flag
            raise NotFoundFlagException(flag_id)

        return self._try_catch(action)

    def save_flags(self, flags: List[Flag]) -> None:
        def action() -> None:
            try:
                self._flag_broker.save_flags(flags)
            except Exception as e:
                raise FlagUnavailableError(str(e)) from e

        self._try_catch(action)
