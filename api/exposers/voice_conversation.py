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
from api.brokers.session_log_entry import SqlAlchemySessionLogEntryBroker
from api.brokers.stt import AzureSttBroker
from api.brokers.topic_covered import SqlAlchemyTopicCoveredBroker
from api.exposers.learner_profile import LearnerProfileController
from api.models.foundations.learner_profile.exceptions import (
    LearnerProfileDependencyException,
    LearnerProfileServiceException,
    LearnerProfileValidationException,
)
from api.models.orchestrations.learner_profile.exceptions import (
    LearnerProfileOrchestrationDependencyException,
    LearnerProfileOrchestrationServiceException,
    LearnerProfileOrchestrationValidationException,
)
from api.models.orchestrations.learner_profile.session_scenario import SessionScenario
from api.services.foundations.flag import FlagService
from api.services.foundations.learner_profile import LearnerProfileService
from api.services.foundations.live_transcript import LiveTranscriptService
from api.services.foundations.mistake_pattern import MistakePatternService
from api.services.foundations.session_log import SessionLogService
from api.services.foundations.session_log_entry import SessionLogEntryService
from api.services.foundations.topic_covered import TopicCoveredService
from api.services.orchestrations.learner_profile import LearnerProfileOrchestrationService
from api.services.orchestrations.voice_conversation import ConversationOrchestrationService
from api.services.orchestrations.voice_conversation._difficulty import get_difficulty_block
from api.services.orchestrations.voice_conversation._pressure import get_pressure_level
from api.services.orchestrations.voice_conversation._priming import format_priming_brief
from api.services.processings.learner_profile import LearnerProfileProcessingService
from api.services.processings.mistake_pattern import MistakePatternProcessingService
from rag.brokers.generation import GeminiGenerationBroker
from rag.services.foundations.generation import GenerationService


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


_GENERIC_SCENARIO_TEXT = "Have a free-flowing conversation at a beginner level."


def _load_scenario(logging_broker: LoggingBroker) -> Optional[SessionScenario]:
    """Build LearnerProfile's full dependency chain (same composition shape
    api/app.py uses for Review's rag dependencies) and ask
    LearnerProfileController for the default suggestion. Returns None if the
    DB or any LearnerProfile dependency is unavailable -- this subprocess
    must still be able to start a conversation even when learner-memory
    data isn't reachable."""
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
            mistake_pattern_processing_service=MistakePatternProcessingService(mistake_pattern_service),
        )
        return LearnerProfileController(orchestrator).suggest_session_scenario()
    except (
        KeyError,
        LearnerProfileOrchestrationValidationException,
        LearnerProfileOrchestrationDependencyException,
        LearnerProfileOrchestrationServiceException,
    ) as e:
        logging_broker.log_warning("Falling back to a generic session scenario: %s", e)
        return None


def _scenario_text(scenario: Optional[SessionScenario], has_difficulty_block: bool = False) -> str:
    """has_difficulty_block: the D6 CEFR block is already in the prompt and is
    the single source for the level, so the proficiency line is dropped."""
    if scenario is None:
        return _GENERIC_SCENARIO_TEXT
    parts = [] if has_difficulty_block else [f"Speak at a {scenario.proficiency_level} proficiency level."]
    if scenario.suggested_topic:
        parts.append(f"Focus this session on: {scenario.suggested_topic}.")
    return " ".join(parts)


def _priming_block(scenario: Optional[SessionScenario], logging_broker: LoggingBroker) -> str:
    """A3: never crashes -- any failure just means no priming brief."""
    try:
        return format_priming_brief(scenario.due_patterns) if scenario else ""
    except Exception as e:  # noqa: BLE001 -- degrade, don't crash (same stance as D6)
        logging_broker.log_warning("Skipping priming brief: %s", e)
        return ""


def _read_cefr_estimate(logging_broker: LoggingBroker) -> Optional[str]:
    """D6: the learner's stored CEFR estimate, or None if unavailable. Same
    degrade-don't-crash stance as _load_scenario -- any profile-read
    failure just means no difficulty block."""
    try:
        # ponytail: builds a second engine beside _load_scenario's (each broker owns its own
        # create_engine); sharing one needs the whole chain built once in _compose_system_prompt
        # and threaded into both helpers -- do that if startup cost/pool count ever matters.
        learner_profile_service = LearnerProfileService(
            SqlAlchemyLearnerProfileBroker(EnvConfigurationBroker().require("DATABASE_URL")),
            logging_broker=logging_broker,
        )
        return learner_profile_service.get_learner_profile().cefr_estimate
    except (
        KeyError,
        LearnerProfileValidationException,
        LearnerProfileDependencyException,
        LearnerProfileServiceException,
    ) as e:
        logging_broker.log_warning("Skipping adaptive-difficulty block: %s", e)
        return None


def _compose_system_prompt(logging_broker: LoggingBroker, pressure_prompt_block: str) -> str:
    base_rules = FilePromptBroker().get_system_prompt()
    override = _read_and_clear_scenario_override()
    # Loaded even when an override wins the scenario line: the A3 priming
    # brief is not user-editable scene text and is appended either way.
    try:
        scenario = _load_scenario(logging_broker)
    except Exception as e:  # noqa: BLE001 -- degrade, don't crash
        logging_broker.log_warning("Scenario load failed: %s", e)
        scenario = None
    difficulty_block = get_difficulty_block(_read_cefr_estimate(logging_broker))
    scenario_text = override or _scenario_text(scenario, has_difficulty_block=bool(difficulty_block))
    prompt = f"{base_rules}\n\nFor this session, practice: {scenario_text}\n\n{pressure_prompt_block}"
    for block in (difficulty_block, _priming_block(scenario, logging_broker)):
        if block:
            prompt = f"{prompt}\n\n{block}"
    return prompt


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

    pressure = get_pressure_level(configuration_broker.get("SESSION_PRESSURE"))

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
                # D5 pressure dial -- SSML prosody rate, e.g. "-15%"/"+12%".
                rate=pressure.tts_rate,
            ),
        )
        llm = GoogleLLMService(
            api_key=configuration_broker.require("GEMINI_API_KEY"),
            settings=GoogleLLMService.Settings(
                model=configuration_broker.get("GEMINI_MODEL", "gemini-flash-lite-latest"),
                system_instruction=_compose_system_prompt(logging_broker, pressure.prompt_block),
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

    # Roadmap A6. Same DATABASE_URL already required just below for
    # session_log_entry_service -- one connection string, reused rather than
    # re-reading the env var, for the same reason _load_scenario's
    # own LearnerProfile chain reuses it above.
    database_url = configuration_broker.require("DATABASE_URL")
    learner_profile_service = LearnerProfileService(
        SqlAlchemyLearnerProfileBroker(database_url), logging_broker=logging_broker
    )

    orchestrator = ConversationOrchestrationService(
        stt_broker=AzureSttBroker(),
        transport=transport,
        tts=tts,
        llm=llm,
        session_log_service=SessionLogService(session_log_broker, logging_broker=logging_broker),
        live_transcript_service=LiveTranscriptService(session_log_broker, logging_broker=logging_broker),
        flag_service=FlagService(JsonFileFlagBroker(), logging_broker=logging_broker),
        session_log_broker=session_log_broker,
        # Roadmap C1/C3. No new configuration: DATABASE_URL is already a
        # required var (CLAUDE.md's env table) and api/app.py -- the only
        # thing that launches this subprocess -- reads it at import, so it
        # is always set by the time we get here. `require()` rather than
        # the soft fallback _load_scenario uses: an unset var is a
        # misconfiguration worth failing loudly on, whereas an unreachable
        # DB is handled downstream (the two write calls in
        # ConversationOrchestrationService are individually guarded, so a
        # dead DB costs the meter one session, not the conversation).
        session_log_entry_service=SessionLogEntryService(
            SqlAlchemySessionLogEntryBroker(database_url),
            logging_broker=logging_broker,
        ),
        # Roadmap A6 -- _estimate_and_persist_cefr_level()'s three
        # dependencies, same GeminiGenerationBroker construction api/app.py
        # uses for Review, plus the same LearnerProfile get-or-create chain
        # built above.
        generation_service=GenerationService(GeminiGenerationBroker(), logging_broker=logging_broker),
        learner_profile_processing_service=LearnerProfileProcessingService(learner_profile_service),
        learner_profile_service=learner_profile_service,
        logging_broker=logging_broker,
        configuration_broker=configuration_broker,
    )
    asyncio.run(orchestrator.run())


if __name__ == "__main__":
    import sys

    if "--selftest" in sys.argv:
        # ponytail: assert-based self-check for the file-driven override
        # logic only -- _load_scenario/_compose_system_prompt need
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
