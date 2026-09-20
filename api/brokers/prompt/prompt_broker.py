"""FilePromptBroker -- data-file-backed PromptBroker."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PROMPTS_DIR = REPO_ROOT / "api" / "data" / "prompts"


class FilePromptBroker:
    """PromptBroker backed by a plain text file under api/data/prompts/.

    `directory` defaults to DEFAULT_PROMPTS_DIR and is only overridden by
    callers that want an isolated location (e.g. tests, once written).
    """

    def __init__(self, directory: Path | None = None) -> None:
        self._directory = directory if directory is not None else DEFAULT_PROMPTS_DIR

    def get_system_prompt(self) -> str:
        return (self._directory / "voice_conversation_system.txt").read_text(encoding="utf-8")

    def get_persona_memory_prompt(self) -> str:
        return (self._directory / "persona_memory_summary.txt").read_text(encoding="utf-8")
