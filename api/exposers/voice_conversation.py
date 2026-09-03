"""Subprocess entrypoint for the live voice conversation.

    python -m api.exposers.voice_conversation

This is the exact command api/brokers/bot_process.py's BOT_COMMAND already
launches. Hand-written, no agent, per CLAUDE.md's Phase 2 Layer-Agent
Mapping — Voice Conversation is a fully manual, supervised port at every
layer. Lives in exposers/ (not a separate controllers/ package) matching
Ingestion's own CLI entrypoint (rag/exposers/ingestion.py) -- CLAUDE.md's
"hand-written, no agent" waiver covers who writes the content, not where
the file lives; both CLI entrypoints get the same mechanical folder move
every other feature's Controller got.

Flask-initiated /stop is handled entirely in the Service
(ConversationOrchestrator._watch_for_stop_signal, polling BotProcessBroker's
stop-flag file) — nothing to wire up here. Ctrl+C still works interactively
via Python's default SIGINT -> KeyboardInterrupt handling.
"""

import asyncio

from dotenv import load_dotenv
from loguru import logger

from api.brokers.flag import JsonFileFlagBroker
from api.brokers.prompt import FilePromptBroker
from api.brokers.session_log import FileSessionLogBroker
from api.brokers.stt import AzureSttBroker
from api.services.foundations.flag import FlagService
from api.services.foundations.live_transcript import LiveTranscriptService
from api.services.foundations.prompt import PromptService
from api.services.foundations.session_log import SessionLogService
from api.services.foundations.stt import SttService
from api.services.orchestrations.voice_conversation import ConversationOrchestrator


def main() -> None:
    load_dotenv()

    # One SessionLogBroker instance shared by both Foundation services that
    # front it (SessionLogService, LiveTranscriptService) -- see
    # api/brokers/session_log/i_session_log_broker.py.
    session_log_broker = FileSessionLogBroker()

    orchestrator = ConversationOrchestrator(
        stt_service=SttService(AzureSttBroker()),
        prompt_service=PromptService(FilePromptBroker()),
        session_log_service=SessionLogService(session_log_broker),
        live_transcript_service=LiveTranscriptService(session_log_broker),
        flag_service=FlagService(JsonFileFlagBroker()),
    )
    logger.info("Voice loop starting — talk into your mic. Ctrl+C to stop.")
    asyncio.run(orchestrator.run())


if __name__ == "__main__":
    main()
