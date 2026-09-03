"""FileSessionLogBroker -- filesystem-backed SessionLogBroker.

SESSION_LOG_DIR / TRANSCRIPT_FILE_PATH moved here verbatim from
api/services/orchestrations/voice_conversation/voice_conversation_service.py
-- same env vars, same defaults, folder move only.
"""

import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[3]

# ponytail: same os.getenv-at-import-time pattern as every other Phase 2
# module. data/ matches FlagBroker's/PracticeLogBroker's own file location
# convention.
DEFAULT_SESSION_LOG_DIR = Path(os.getenv("SESSION_LOG_DIR", str(REPO_ROOT / "data" / "session_logs")))
DEFAULT_TRANSCRIPT_FILE_PATH = Path(
    os.getenv("TRANSCRIPT_FILE_PATH", str(REPO_ROOT / "data" / "live_transcript.jsonl"))
)


class FileSessionLogBroker:
    """SessionLogBroker backed by plain files under data/.

    `session_log_dir`/`transcript_file_path` default to the env-configured
    paths and are only overridden by callers that want isolated locations
    (e.g. tests, once written).
    """

    def __init__(
        self,
        session_log_dir: Path | None = None,
        transcript_file_path: Path | None = None,
    ) -> None:
        self._session_log_dir = session_log_dir if session_log_dir is not None else DEFAULT_SESSION_LOG_DIR
        self._transcript_file_path = (
            transcript_file_path if transcript_file_path is not None else DEFAULT_TRANSCRIPT_FILE_PATH
        )

    def write_session_log(self, content: str) -> Path:
        self._session_log_dir.mkdir(parents=True, exist_ok=True)
        log_path = self._session_log_dir / f"{datetime.now():%Y-%m-%d-%H%M%S}.log"
        log_path.write_text(content, encoding="utf-8")
        return log_path

    def clear_transcript(self) -> None:
        self._transcript_file_path.parent.mkdir(parents=True, exist_ok=True)
        self._transcript_file_path.write_text("", encoding="utf-8")

    def append_transcript_line(self, line: str) -> None:
        with open(self._transcript_file_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
