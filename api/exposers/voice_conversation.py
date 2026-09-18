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
(ConversationOrchestrationService._watch_for_stop_signal, polling BotProcessBroker's
stop-flag file) — nothing to wire up here. Ctrl+C still works interactively
via Python's default SIGINT -> KeyboardInterrupt handling.

Audit H4 (2026-09-10): transport/tts/llm are built here now, not inside
ConversationOrchestrationService -- this is the composition root, so it's the one
place that should import pipecat's Azure/Google service classes and read
their credentials + the system prompt. A missing/invalid credential now
raises KeyError here, before the orchestrator or pipeline exist at all,
logged the same way _try_catch used to log it (as
VoiceConversationConfigError) but as a raw KeyError -- nothing outside this
feature catches that exception by type, so the change is observable only
in this subprocess's own log/traceback, not to any caller.

LearnerProfile Phase 3 (2026-09-17, see decisions/dynamic-bot-behavior-and-
learner-memory.md): the system prompt is now composed, not static. A
scenario override written by SessionLifecycleService's /start (see
BotProcessBroker.start()) is read here if present and consumed (one-shot,
same pattern as the stop-signal file); otherwise this composition root
builds the full LearnerProfile dependency chain itself (same shape
api/app.py uses for Review's rag dependencies) and asks
LearnerProfileController directly for the default suggestion. Either way,
the fixed output-format rules (TTS formatting, flag emission) stay exactly
as they were in the static .txt file -- only the "what to talk about"
section is now scenario-driven, per the design record's Phase 3 scope.
"""

import asyncio
from pathlib import Path
from typing import Optional

from pipecat.services.azure.tts import AzureTTSService
from pipecat.services.google.llm import GoogleLLMService
from pipecat.transcriptions.language import Language
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams

from api.brokers.bot_process.bot_process_broker import SCENARIO_OVERRIDE_FILE_PATH
from api.brokers.configuration import EnvConfigurationBroker
from api.brokers.flag import JsonFileFlagBroker
from api.brokers.learner_profile import SqlAlchemyLearnerProfileBroker
from api.brokers.logging import LoggingBroker, StdlibLoggingBroker
from api.brokers.mistake_pattern.mistake_pattern_broker import SqlAlchemyMistakePatternBroker
from api.brokers.prompt import FilePromptBroker
from api.brokers.session_log import FileSessionLogBroker
from api.brokers.stt import AzureSttBroker
from api.brokers.topic_covered import SqlAlchemyTopicCoveredBroker
from api.exposers.learner_profile import LearnerProfileController
from api.models.orchestrations.learner_profile.exceptions import (
    LearnerProfileOrchestrationDependencyException,
    LearnerProfileOrchestrationServiceException,
    LearnerProfileOrchestrationValidationException,
)
from api.services.foundations.flag import FlagService
from api.services.foundations.learner_profile import LearnerProfileService
from api.services.foundations.live_transcript import LiveTranscriptService
from api.services.foundations.mistake_pattern import MistakePatternService
from api.services.foundations.session_log import SessionLogService
from api.services.foundations.topic_covered import TopicCoveredService
from api.services.orchestrations.learner_profile import LearnerProfileOrchestrationService
from api.services.orchestrations.voice_conversation import ConversationOrchestrationService
from api.services.processings.learner_profile import LearnerProfileProcessingService


def _read_and_clear_scenario_override(path: Path = SCENARIO_OVERRIDE_FILE_PATH) -> Optional[str]:
    """One-shot read of the scenario-override file SessionLifecycleService's
    /start may have written (see BotProcessBroker.start()). Deleted after
    reading, same as the stop-signal file, so a stale override never leaks
    into a later manually-started session.

    `path` is only overridden by the --selftest block below -- `python -m`
    loads this module twice under different names (once as __main__, once
    as api.exposers.voice_conversation), so patching the module-level
    constant by string path doesn't reach the copy actually running;
    parameter injection sidesteps that entirely."""
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    path.unlink(missing_ok=True)
    return text


def _default_scenario_text(logging_broker: LoggingBroker) -> str:
    """Build LearnerProfile's full dependency chain (same composition shape
    api/app.py uses for Review's rag dependencies) and ask
    LearnerProfileController for the default suggestion. Falls back to a
    generic line if the DB or any LearnerProfile dependency is unavailable
    -- this subprocess must still be able to start a conversation even when
    learner-memory data isn't reachable."""
    try:
        connection_string = EnvConfigurationBroker().require("DATABASE_URL")
        learner_profile_service = LearnerProfileService(
            SqlAlchemyLearnerProfileBroker(connection_string), logging_broker=logging_broker
        )
        mistake_pattern_service = MistakePatternService(
            SqlAlchemyMistakePatternBroker(connection_string), logging_broker=logging_broker
        )
        topic_covered_service = TopicCoveredService(
            SqlAlchemyTopicCoveredBroker(connection_string), logging_broker=logging_broker
        )
        flag_service = FlagService(JsonFileFlagBroker(), logging_broker=logging_broker)
        orchestrator = LearnerProfileOrchestrationService(
            LearnerProfileProcessingService(learner_profile_service),
            mistake_pattern_service,
            topic_covered_service,
            flag_service,
            logging_broker=logging_broker,
        )
        scenario = LearnerProfileController(orchestrator).suggest_session_scenario()
    except (
        KeyError,
        LearnerProfileOrchestrationValidationException,
        LearnerProfileOrchestrationDependencyException,
        LearnerProfileOrchestrationServiceException,
    ) as e:
        logging_broker.log_warning("Falling back to a generic session scenario: %s", e)
        return "Have a free-flowing conversation at a beginner level."

    parts = [f"Speak at a {scenario.proficiency_level} proficiency level."]
    if scenario.suggested_topic:
        parts.append(f"Focus this session on: {scenario.suggested_topic}.")
    return " ".join(parts)


def _compose_system_prompt(logging_broker: LoggingBroker) -> str:
    base_rules = FilePromptBroker().get_system_prompt()
    scenario_text = _read_and_clear_scenario_override() or _default_scenario_text(logging_broker)
    return f"{base_rules}\n\nFor this session, practice: {scenario_text}"


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
                system_instruction=_compose_system_prompt(logging_broker),
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

    orchestrator = ConversationOrchestrationService(
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
    import sys

    if "--selftest" in sys.argv:
        # ponytail: assert-based self-check for the file-driven override
        # logic only -- _default_scenario_text/_compose_system_prompt need
        # a real DB and are covered by LearnerProfileOrchestrationService's
        # own unit suite plus this feature's manual hardware-verify gate
        # (CLAUDE.md: Voice Conversation, no agent, any layer).
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            override_path = Path(tmp) / "scenario_override.txt"
            assert _read_and_clear_scenario_override(override_path) is None

            override_path.write_text("practice ordering coffee", encoding="utf-8")
            assert _read_and_clear_scenario_override(override_path) == "practice ordering coffee"
            assert not override_path.exists()
        print("OK")
    else:
        main()
