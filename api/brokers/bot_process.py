"""Broker for the voice-conversation subprocess.

Owns the OS process handle for `python -m api.controllers.voice_conversation`
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

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Protocol

REPO_ROOT = Path(__file__).resolve().parents[2]
BOT_COMMAND = [sys.executable, "-m", "api.controllers.voice_conversation"]
STOP_SIGNAL_FILE_PATH = Path(os.getenv("STOP_SIGNAL_FILE_PATH", str(REPO_ROOT / "data" / "stop_signal")))

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


class SubprocessBotProcessBroker:
    """BotProcessBroker backed by subprocess.Popen.

    `command`/`cwd` default to the real voice-conversation entrypoint and
    are only overridden by tests, which substitute a short-lived stdlib
    command to exercise start/stop/poll mechanics deterministically without
    a mic, Azure credentials, or the (not-yet-built) controller module.
    """

    def __init__(
        self,
        command: Optional[List[str]] = None,
        cwd: Optional[Path] = None,
        stop_signal_path: Optional[Path] = None,
    ) -> None:
        self._command = command if command is not None else BOT_COMMAND
        self._cwd = cwd if cwd is not None else REPO_ROOT
        self._stop_signal_path = stop_signal_path if stop_signal_path is not None else STOP_SIGNAL_FILE_PATH
        self._process: Optional[subprocess.Popen] = None
        self._last_return_code: Optional[int] = None

    def start(self) -> None:
        self._process = subprocess.Popen(self._command, cwd=str(self._cwd))

    def send_graceful_signal(self) -> None:
        self._stop_signal_path.parent.mkdir(parents=True, exist_ok=True)
        self._stop_signal_path.touch()

    def terminate(self) -> None:
        self._process.terminate()

    def kill(self) -> None:
        self._process.kill()

    def wait(self, timeout: float) -> None:
        self._process.wait(timeout=timeout)

    def is_running(self) -> bool:
        if self._process is None:
            return False
        return_code = self._process.poll()
        if return_code is not None:
            self._last_return_code = return_code
        return return_code is None

    def get_last_return_code(self) -> Optional[int]:
        return self._last_return_code
