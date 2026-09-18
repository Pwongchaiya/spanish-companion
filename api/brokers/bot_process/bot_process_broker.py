"""SubprocessBotProcessBroker — subprocess.Popen-backed BotProcessBroker."""

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

REPO_ROOT = Path(__file__).resolve().parents[3]
BOT_COMMAND = [sys.executable, "-m", "api.exposers.voice_conversation"]
STOP_SIGNAL_FILE_PATH = Path(os.getenv("STOP_SIGNAL_FILE_PATH", str(REPO_ROOT / "data" / "stop_signal")))
SCENARIO_OVERRIDE_FILE_PATH = Path(
    os.getenv("SCENARIO_OVERRIDE_FILE_PATH", str(REPO_ROOT / "data" / "scenario_override.txt"))
)


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
        scenario_override_path: Optional[Path] = None,
    ) -> None:
        self._command = command if command is not None else BOT_COMMAND
        self._cwd = cwd if cwd is not None else REPO_ROOT
        self._stop_signal_path = stop_signal_path if stop_signal_path is not None else STOP_SIGNAL_FILE_PATH
        self._scenario_override_path = (
            scenario_override_path if scenario_override_path is not None else SCENARIO_OVERRIDE_FILE_PATH
        )
        self._process: Optional[subprocess.Popen] = None
        self._last_return_code: Optional[int] = None

    def start(self, scenario_text: Optional[str] = None) -> None:
        if scenario_text is not None:
            self._scenario_override_path.parent.mkdir(parents=True, exist_ok=True)
            self._scenario_override_path.write_text(scenario_text, encoding="utf-8")
        else:
            self._scenario_override_path.unlink(missing_ok=True)
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


if __name__ == "__main__":
    # ponytail: assert-based self-check for the scenario-override file
    # write/clear logic -- no framework, no real subprocess spawn (patches
    # Popen out). Full start/stop/poll escalation is covered by
    # ConversationSessionService's own test suite instead.
    import tempfile
    from unittest.mock import patch

    with tempfile.TemporaryDirectory() as tmp:
        override_path = Path(tmp) / "scenario_override.txt"
        broker = SubprocessBotProcessBroker(
            command=[sys.executable, "-c", "pass"], scenario_override_path=override_path
        )
        with patch("subprocess.Popen"):
            broker.start("practice ordering coffee")
            assert override_path.read_text(encoding="utf-8") == "practice ordering coffee"

            broker.start(None)
            assert not override_path.exists()
    print("OK")
