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

Audit H4 (2026-09-10): transport/tts/llm are built here now, not inside
ConversationOrchestrator -- this is the composition root, so it's the one
place that should import pipecat's Azure/Google service classes and read
their credentials + the system prompt. A missing/invalid credential now
raises KeyError here, before the orchestrator or pipeline exist at all,
logged the same way _try_catch used to log it (as
VoiceConversationConfigError) but as a raw KeyError -- nothing outside this
feature catches that exception by type, so the change is observable only
in this subprocess's own log/traceback, not to any caller.
"""

import asyncio

from pipecat.services.azure.tts import AzureTTSService
from pipecat.services.google.llm import GoogleLLMService
from pipecat.transcriptions.language import Language
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams

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

    try:
        transport = LocalAudioTransport(
            LocalAudioTransportParams(audio_in_enabled=True, audio_out_enabled=True)
        )
        tts = AzureTTSService(
            api_key=configuration_broker.require("AZURE_SPEECH_KEY"),
            region=configuration_broker.require("AZURE_SPEECH_REGION"),
            settings=AzureTTSService.Settings(
                # Multilingual voice — speaks both the Spanish phrases and the
                # English explanations naturally, instead of an English accent
                # on a Spanish-only voice.
                voice=configuration_broker.get("AZURE_TTS_VOICE", "es-ES-XimenaMultilingualNeural"),
                language=Language.ES_ES,
            ),
        )
        llm = GoogleLLMService(
            api_key=configuration_broker.require("GEMINI_API_KEY"),
            settings=GoogleLLMService.Settings(
                model=configuration_broker.get("GEMINI_MODEL", "gemini-flash-lite-latest"),
                system_instruction=FilePromptBroker().get_system_prompt(),
            ),
            # A slow first chunk (network blip, API-side latency) otherwise drops
            # the turn silently with no assistant reply ever recorded — the user
            # just keeps talking into what looks like silence, and each unanswered
            # turn piles onto a growing, non-alternating context that makes the
            # next request slower too. One retry breaks that spiral.
            retry_on_timeout=True,
        )
    except KeyError as e:
        logging_broker.log_error(f"Missing required configuration: {e}")
        raise

    orchestrator = ConversationOrchestrator(
        stt_broker=AzureSttBroker(),
        transport=transport,
        tts=tts,
        llm=llm,
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
