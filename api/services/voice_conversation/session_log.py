"""Session transcript logging for Conversation Mode.

Writes a timestamped, human-readable log of the conversation + flags on
session end, for manual review per this step's testing standard (no
automated transcript checks yet — see CLAUDE.md Testing Standards). Split
out of voice_conversation_service.py for single-responsibility.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from pipecat.processors.aggregators.llm_context import LLMContext

from api.models.flag import Flag

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[3]

# ponytail: same os.getenv-at-import-time pattern as every other Phase 2
# module (load_dotenv() then os.getenv with a string default). data/ matches
# FlagBroker's/PracticeLogBroker's own file location convention.
SESSION_LOG_DIR = Path(os.getenv("SESSION_LOG_DIR", str(REPO_ROOT / "data" / "session_logs")))


def message_text(content) -> str:
    """Flatten an LLMContextMessage's content (a string, or a list of
    OpenAI-style content blocks) into plain text for the log."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return str(content)


def save_session_log(context: LLMContext, flags: List[Flag]) -> Optional[Path]:
    """Write the session's conversation turns to a timestamped file under
    data/session_logs/, for manual review per this step's testing standard
    (no automated transcript checks yet — see CLAUDE.md Testing Standards)."""
    turns = [
        f"[{message['role']}] {message_text(message['content'])}"
        for message in context.messages
        if isinstance(message, dict) and message["role"] in ("user", "assistant")
    ]
    if not turns:
        return None

    output_lines = turns[:]
    if flags:
        output_lines.append("--- flags ---")
        for flag in flags:
            output_lines.append(
                f"[{flag.category}] said: \"{flag.said}\" -> corrected: \"{flag.corrected}\""
            )

    SESSION_LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = SESSION_LOG_DIR / f"{datetime.now():%Y-%m-%d-%H%M%S}.log"
    log_path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")
    return log_path
