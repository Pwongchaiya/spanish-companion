"""Foundation service for the voice-conversation session lifecycle.

Composes BotProcessBroker's raw primitives (api/brokers/bot_process/) into
the policy the broker deliberately leaves out: double-start refusal, the
graceful -> terminate -> kill stop escalation, and the ready-vs-running
distinction. See BotProcessBroker's docstring for the composition order this
class implements: start() -> is_running() -> send_graceful_signal() ->
wait(timeout) -> terminate() -> wait(timeout) -> kill().

Single broker dependency -> Foundation layer, not Orchestration, per
CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers.

Split into a base logic file plus Validations/Exceptions mixins (this file,
session_lifecycle_service_validations.py, session_lifecycle_service_exceptions.py)
-- mirrors C#'s `partial class` merging EntitlementService.cs /
.Validations.cs / .Exeptions.cs into one class. The concrete class is
declared directly in THIS file, inheriting the other two mixins by name --
no separate "_Base" intermediate class, no composition step in __init__.py.
Matches LearnerProfileService/MistakePatternService's rebuilt shape: one
class, declared once, `class X(XExceptions, XValidations, IX):`, constructor
and public methods on it directly. (The previous
`_ConversationSessionServiceBase` + __init__.py composition step was the
invented-`_ServiceBase` pattern CLAUDE.md explicitly disallows -- removed.)

start() and stop() are the ONLY methods wrapped with `_try_catch` (defined
in the Exceptions mixin) -- each public method's entire body is an inline
nested closure passed straight to `_try_catch`, not a separate `_do_thing`
private method with its own local try/except. get_status() has never raised
domain exceptions and stays unwrapped, matching the previous behaviour --
_try_catch here doesn't propagate fn()'s return value (see
session_lifecycle_service_exceptions.py), which only matters if a wrapped
method needs to return something; start/stop both return None so this is a
no-op distinction, left alone per the "leave *_exceptions.py alone" brief.
"""

import subprocess
import time
from typing import Callable, Optional

from api.brokers.bot_process import BotProcessBroker
from api.brokers.configuration import ConfigurationBroker, EnvConfigurationBroker
from api.brokers.logging import LoggingBroker
from api.models.foundations.session_lifecycle.session_status import SessionStatus
from api.services.foundations.session_lifecycle.i_session_lifecycle_service import (
    SessionLifecycleService as ISessionLifecycleService,
)
from api.services.foundations.session_lifecycle.session_lifecycle_service_exceptions import (
    ConversationSessionServiceExceptions,
)
from api.services.foundations.session_lifecycle.session_lifecycle_service_validations import (
    ConversationSessionServiceValidations,
)

# ponytail: no IPC channel from the subprocess back to this service yet --
# that lands when Voice Conversation's subprocess side is manually ported.
# Until then "ready" is a time-based heuristic: running continuously for
# this long without exiting is taken as "the pipeline is probably warm".
# 16s matches Phase 1's observed STT/TTS/LLM warm-up time -- the exact bug
# (process started != pipeline warm) this ready/running split exists to fix,
# per the Phase 2 architecture decision record. Replace with real
# subprocess-reported readiness once that IPC exists.


class ConversationSessionService(
    ConversationSessionServiceExceptions,
    ConversationSessionServiceValidations,
    ISessionLifecycleService,
):
    """Owns lifecycle policy for the voice-conversation subprocess.

    Validation checks are named methods (defined in the Validations mixin)
    rather than inlined, mirroring EntitlementService.cs:31-41.
    """

    def __init__(
        self,
        broker: BotProcessBroker,
        time_source: Callable[[], float] = time.monotonic,
        *,
        logging_broker: LoggingBroker,
        configuration_broker: ConfigurationBroker = EnvConfigurationBroker(),
    ) -> None:
        self._broker = broker
        self._time_source = time_source
        self._logging_broker = logging_broker
        self._configuration_broker = configuration_broker
        self._started_at: Optional[float] = None
        self._last_stop_graceful: Optional[bool] = None

    def start(self) -> None:
        def action() -> None:
            self._validate_not_already_running()
            self._broker.start()
            self._started_at = self._time_source()

        self._try_catch(action)

    def stop(self) -> None:
        def action() -> None:
            self._validate_currently_running()

            graceful_timeout_seconds = float(
                self._configuration_broker.get("SESSION_GRACEFUL_TIMEOUT_SECONDS", "5")
            )
            terminate_timeout_seconds = float(
                self._configuration_broker.get("SESSION_TERMINATE_TIMEOUT_SECONDS", "2")
            )

            self._broker.send_graceful_signal()
            if self._wait_quietly(graceful_timeout_seconds):
                self._last_stop_graceful = True
                return

            self._broker.terminate()
            if self._wait_quietly(terminate_timeout_seconds):
                self._last_stop_graceful = False
                return

            self._broker.kill()
            # ponytail: SIGKILL/TerminateProcess can't be intercepted or
            # ignored by the child, so this wait is not expected to time
            # out. If it somehow does, that's an OS-level anomaly outside
            # this feature's two-exception vocabulary -- _try_catch's
            # explicit `except subprocess.TimeoutExpired: raise` clause
            # carves this out from the generic wrap-and-log path and lets
            # it propagate raw, rather than inventing a third leaf
            # exception to wrap it.
            self._broker.wait(terminate_timeout_seconds)
            self._last_stop_graceful = False

        self._try_catch(action)

    def get_status(self) -> SessionStatus:
        ready_warmup_seconds = float(self._configuration_broker.get("SESSION_READY_WARMUP_SECONDS", "16"))
        running = self._broker.is_running()
        ready = bool(
            running
            and self._started_at is not None
            and self._time_source() - self._started_at >= ready_warmup_seconds
        )
        # If process was started but is no longer running and stop() wasn't called,
        # it crashed unexpectedly. If never started, graceful remains None.
        graceful = self._last_stop_graceful
        if not running and self._last_stop_graceful is None and self._started_at is not None:
            graceful = False
        return SessionStatus(running=running, ready=ready, graceful=graceful)

    def _wait_quietly(self, timeout: float) -> bool:
        """Wait up to `timeout` seconds for the process to exit.

        Returns True if it exited, False if it's still running. Never
        raises -- subprocess.TimeoutExpired just means "still running",
        which is the escalation trigger, not an error.
        """
        try:
            self._broker.wait(timeout)
            return True
        except subprocess.TimeoutExpired:
            return False
