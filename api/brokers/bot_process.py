"""Broker for the voice-conversation subprocess.

Owns the OS process handle for `python -m api.controllers.voice_conversation`
(the Phase 2 successor to Phase 1's `voice/bot.py`, launched the same way
Phase 1's `ui/app.py` launched it). No persistence, no business logic —
double-start refusal and the graceful/terminate/kill escalation policy
(timeouts, retry order) belong to the Foundation service
(`ConversationSessionService`) built next, which composes the raw
primitives below. This broker only wraps subprocess.Popen calls; it does
not decide when to use them.

Windows signal mechanics ported as-is from the hardware-verified Phase 1
fix in `ui/app.py` (`_start_voice_process` / `_stop_voice_process`):
CREATE_NEW_PROCESS_GROUP lets the parent later send CTRL_BREAK_EVENT
(SIGBREAK), which the child subprocess converts to KeyboardInterrupt to run
its shutdown `finally` block (flag persistence). Unlike SIGINT, Windows has
no default handler for it, and an unhandled SIGBREAK kills the child
outright, skipping that cleanup — this is why the signal dance exists.
"""

import signal
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Protocol

REPO_ROOT = Path(__file__).resolve().parents[2]
BOT_COMMAND = [sys.executable, "-m", "api.controllers.voice_conversation"]

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

    def start(self) -> None:
        """Launch the subprocess. Non-blocking."""
        ...

    def send_graceful_signal(self) -> None:
        """Send the platform graceful-shutdown signal (SIGBREAK on Windows,
        SIGTERM elsewhere). Does not wait for exit."""
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


class SubprocessBotProcessBroker:
    """BotProcessBroker backed by subprocess.Popen.

    `command`/`cwd` default to the real voice-conversation entrypoint and
    are only overridden by tests, which substitute a short-lived stdlib
    command to exercise start/stop/poll mechanics deterministically without
    a mic, Azure credentials, or the (not-yet-built) controller module.
    """

    def __init__(self, command: Optional[List[str]] = None, cwd: Optional[Path] = None) -> None:
        self._command = command if command is not None else BOT_COMMAND
        self._cwd = cwd if cwd is not None else REPO_ROOT
        self._process: Optional[subprocess.Popen] = None

    def start(self) -> None:
        # ponytail: Windows-only creationflags kwarg is mechanically required
        # for CTRL_BREAK_EVENT delivery in send_graceful_signal(); no
        # cross-platform stdlib equivalent exists, so this stays.
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
        self._process = subprocess.Popen(
            self._command,
            cwd=str(self._cwd),
            creationflags=creationflags,
        )

    def send_graceful_signal(self) -> None:
        graceful_signal = signal.CTRL_BREAK_EVENT if sys.platform == "win32" else signal.SIGTERM
        self._process.send_signal(graceful_signal)

    def terminate(self) -> None:
        self._process.terminate()

    def kill(self) -> None:
        self._process.kill()

    def wait(self, timeout: float) -> None:
        self._process.wait(timeout=timeout)

    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None
