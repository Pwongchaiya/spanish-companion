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

from api.brokers.configuration import EnvConfigurationBroker
from api.brokers.flag import JsonFileFlagBroker
from api.brokers.logging import StdlibLoggingBroker
from api.brokers.prompt import FilePromptBroker
from api.brokers.session_log import FileSessionLogBroker
from api.brokers.stt import AzureSttBroker
from api.services.foundations.flag import FlagService
from api.services.foundations.live_transcript import LiveTranscriptService
from api.services.foundations.session_log import SessionLogService
from api.services.orchestrations.voice_conversation import ConversationOrchestrator


def main() -> None:
    # This CLI entrypoint is its own composition root: one LoggingBroker and
    # one ConfigurationBroker built here and threaded down, the same shape
    # api/app.py uses. EnvConfigurationBroker calls load_dotenv() itself, so
    # there is no separate load_dotenv() here any more.
    logging_broker = StdlibLoggingBroker()
    configuration_broker = EnvConfigurationBroker()

    # One SessionLogBroker instance shared by every Foundation service that
    # fronts it (SessionLogService, LiveTranscriptService), plus the
    # orchestrator itself for the turn-state signal
    # -- see api/brokers/session_log/i_session_log_broker.py.
    session_log_broker = FileSessionLogBroker()

    orchestrator = ConversationOrchestrator(
        stt_broker=AzureSttBroker(),
        prompt_broker=FilePromptBroker(),
        session_log_service=SessionLogService(session_log_broker, logging_broker=logging_broker),
        live_transcript_service=LiveTranscriptService(session_log_broker, logging_broker=logging_broker),
        flag_service=FlagService(JsonFileFlagBroker(), logging_broker=logging_broker),
        session_log_broker=session_log_broker,
        logging_broker=logging_broker,
        configuration_broker=configuration_broker,
    )
    asyncio.run(orchestrator.run())


if __name__ == "__main__":
    main()
