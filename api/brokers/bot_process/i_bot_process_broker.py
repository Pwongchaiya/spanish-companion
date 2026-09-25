"""Broker for the voice-conversation subprocess.

Owns the OS process handle for `python -m api.exposers.voice_conversation`
(the Phase 2 successor to Phase 1's `voice/bot.py`, launched the same way
Phase 1's `ui/app.py` launched it). No persistence, no business logic —
double-start refusal and the graceful/terminate/kill escalation policy
(timeouts, retry order) belong to the Foundation service
(`ConversationSessionService`) built next, which composes the raw
primitives below. This broker only wraps subprocess.Popen calls; it does
not decide when to use them.

Graceful shutdown uses a stop-flag file, not a Windows console signal.
Phase 1's approach (CTRL_BREAK_EVENT / SIGBREAK) was ported here first, but
hardware-verified via a real terminal keystroke, not this process's actual
usage — a separate parent process programmatically calling
Popen.send_signal(CTRL_BREAK_EVENT) on a child it spawned. That specific
pattern was confirmed broken via isolated repro (2026-08-29, no pipecat
involved): GenerateConsoleCtrlEvent's console-attachment requirements make
it unreliable outside a real interactive console, and even a real terminal
didn't rescue it. A polled stop-flag file has no such dependency and works
identically cross-platform.
"""

from typing import Optional, Protocol

# ponytail: scenario_text crosses the process boundary via a one-shot file,
# mirroring the existing stop-flag file convention (see
# ConversationOrchestrationService._watch_for_stop_signal) -- the subprocess
# is launched with a fixed argv (bot_process_broker.py's BOT_COMMAND), so a
# file is the only channel available without inventing a new IPC mechanism.

# ponytail: no double-start exception type here — that's
# ConversationSessionService vocabulary (it owns the refusal decision), and
# nothing calls one yet. Add it in that service's own module when it's built,
# per exception-hierarchy-skill's per-entity/per-service exception pattern.


class BotProcessBroker(Protocol):
    """External-resource boundary for the voice-conversation subprocess.

    Raw primitives only — no escalation policy. The service composes
    start() -> is_running() -> send_graceful_signal() -> wait(timeout) ->
    terminate() -> wait(timeout) -> kill() itself.
    """

    def start(
        self,
        scenario_text: Optional[str] = None,
        pressure_level: Optional[str] = None,
        variant: Optional[str] = None,
        scenario_slug: Optional[str] = None,
        persona: Optional[str] = None,
    ) -> None:
        """Launch the subprocess. Non-blocking.

        `scenario_text`, if given, is written to a one-shot file the child
        reads at startup to compose its system prompt -- see the module
        docstring. If None, the child falls back to its own default
        scenario suggestion.

        `pressure_level` (D5, "gentle"/"normal"/"push"), if given, is
        injected as a SESSION_PRESSURE env var into the child process --
        a structured value, not prose, so it can't travel via the
        scenario-text file. If None, the child falls back to "normal".

        `variant` (D2, a key of api/data/spanish_variants.py), if given, is
        injected the same way as SESSION_VARIANT. If None, the child falls
        back to "neutral".

        `scenario_slug` (D4, a slug of api/data/roleplay_scenarios.py), if
        given, is injected as SESSION_SCENARIO_SLUG so the child can record
        it on its session_log row.

        `persona` (a slug of api/data/personas.py), if given, is injected as
        SESSION_PERSONA. If None, the child runs with no persona.
        """
        ...

    def send_graceful_signal(self) -> None:
        """Request graceful shutdown via the stop-flag file the child polls
        for. Does not wait for exit."""
        ...

    def terminate(self) -> None:
        """Send a hard terminate signal. Does not wait for exit."""
        ...

    def kill(self) -> None:
        """Send SIGKILL. Does not wait for exit."""
        ...

    def wait(self, timeout: float) -> None:
        """Block until the process exits or `timeout` elapses.

        Raises:
            subprocess.TimeoutExpired: still running when `timeout` elapses.
        """
        ...

    def is_running(self) -> bool:
        """Poll process state. Non-blocking."""
        ...

    def get_last_return_code(self) -> Optional[int]:
        """Get the return code of the last process exit, if any.

        Returns None if the process is still running or has never started.
        Lets the service distinguish crashed exits from graceful ones.
        """
        ...
