"""Foundation service for the voice-conversation session lifecycle.

Composes BotProcessBroker's raw primitives (api/brokers/bot_process.py) into
the policy the broker deliberately leaves out: double-start refusal, the
graceful -> terminate -> kill stop escalation, and the ready-vs-running
distinction. See BotProcessBroker's docstring for the composition order this
class implements: start() -> is_running() -> send_graceful_signal() ->
wait(timeout) -> terminate() -> wait(timeout) -> kill().

Single broker dependency -> Foundation layer, not Orchestration, per
CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers.
"""

import os
import subprocess
import time
from typing import Callable, Optional

from dotenv import load_dotenv

from api.brokers.bot_process import BotProcessBroker
from api.errors import ApiError
from api.models.session_status import SessionStatus

load_dotenv()

# ponytail: two knobs -> plain os.getenv at import time, no settings object.
# Matches rag/db.py's / rag/retrieve.py's existing pattern (load_dotenv()
# then os.getenv with a string default, cast at the read site). Add a real
# config module when a third knob shows up.
GRACEFUL_TIMEOUT_SECONDS = float(os.getenv("SESSION_GRACEFUL_TIMEOUT_SECONDS", "5"))
TERMINATE_TIMEOUT_SECONDS = float(os.getenv("SESSION_TERMINATE_TIMEOUT_SECONDS", "2"))

# ponytail: no IPC channel from the subprocess back to this service yet --
# that lands when Voice Conversation's subprocess side is manually ported.
# Until then "ready" is a time-based heuristic: running continuously for
# this long without exiting is taken as "the pipeline is probably warm".
# 16s matches Phase 1's observed STT/TTS/LLM warm-up time -- the exact bug
# (process started != pipeline warm) this ready/running split exists to fix,
# per the Phase 2 architecture decision record. Replace with real
# subprocess-reported readiness once that IPC exists.
READY_WARMUP_SECONDS = float(os.getenv("SESSION_READY_WARMUP_SECONDS", "16"))


class SessionAlreadyRunningException(ApiError):
    """Raised by start() when a session is already active.

    BotProcessBroker.start() has no such guard by design (see its
    docstring) -- this service owns the refusal.
    """

    def __init__(self) -> None:
        super().__init__("A conversation session is already running")


class SessionNotRunningException(ApiError):
    """Raised by stop() when there is no active session to stop.

    Deliberately fail-fast rather than a silent no-op: symmetric with
    start()'s SessionAlreadyRunningException, and a stop() call against a
    session the caller believes is running but isn't signals a client-side
    state mismatch worth surfacing immediately rather than swallowing.
    """

    def __init__(self) -> None:
        super().__init__("No conversation session is running")


class ConversationSessionService:
    """Owns lifecycle policy for the voice-conversation subprocess."""

    def __init__(
        self,
        broker: BotProcessBroker,
        time_source: Callable[[], float] = time.monotonic,
    ) -> None:
        self._broker = broker
        self._time_source = time_source
        self._started_at: Optional[float] = None
        self._last_stop_graceful: Optional[bool] = None

    def start(self) -> None:
        if self._broker.is_running():
            raise SessionAlreadyRunningException()
        self._broker.start()
        self._started_at = self._time_source()

    def stop(self) -> None:
        if not self._broker.is_running():
            raise SessionNotRunningException()

        self._broker.send_graceful_signal()
        if self._wait_quietly(GRACEFUL_TIMEOUT_SECONDS):
            self._last_stop_graceful = True
            return

        self._broker.terminate()
        if self._wait_quietly(TERMINATE_TIMEOUT_SECONDS):
            self._last_stop_graceful = False
            return

        self._broker.kill()
        # ponytail: SIGKILL/TerminateProcess can't be intercepted or ignored
        # by the child, so this wait is not expected to time out. If it
        # somehow does, that's an OS-level anomaly outside this feature's
        # two-exception vocabulary -- let subprocess.TimeoutExpired propagate
        # rather than inventing a third exception type to wrap it.
        self._broker.wait(TERMINATE_TIMEOUT_SECONDS)
        self._last_stop_graceful = False

    def get_status(self) -> SessionStatus:
        running = self._broker.is_running()
        ready = bool(
            running
            and self._started_at is not None
            and self._time_source() - self._started_at >= READY_WARMUP_SECONDS
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
