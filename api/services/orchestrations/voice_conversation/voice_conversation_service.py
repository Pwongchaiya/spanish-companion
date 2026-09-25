"""Service layer for the live voice conversation — Conversation Mode.

Fully manual, supervised port of Phase 1's `voice/bot.py`. No agent built
any part of this file (see CLAUDE.md's Phase 2 Layer-Agent Mapping): it
carries three hardware-verified fixes no agent can discover or test —
echo suppression, the 44100/24000Hz sample-rate mismatch, and periodic
flag persistence — gated on a real mic/hardware test, same method as
Phase 1. Graceful stop on `/stop` uses a polled stop-flag file (see
`_watch_for_stop_signal`), not Phase 1's Windows SIGBREAK port — that
mechanism was confirmed broken via isolated repro, 2026-08-29 (see
api/brokers/bot_process/bot_process_broker.py's module docstring).

Wave 8 six-layer migration (hand-written, no agent, per CLAUDE.md): this
Orchestration service coordinates SessionLogService,
LiveTranscriptService, and FlagService (TurnStateService was added
post-Wave-8, see decisions/tri-nature-gate-design.md's follow-up 2, and
deleted in W3 as a pass-through) — replacing what used to be inline pipecat/Azure construction and
free-function file I/O directly in this class. STT is taken as a bare
SttBroker: W3 of the architecture conformance audit (M5) deleted the
pure-pass-through SttService that used to front it. LLM and TTS are
injected as already-built bare pipecat service objects (H4 of the audit
moved their construction, and the credential/prompt reads it needed, to
the composition root -- api/exposers/voice_conversation.py -- alongside
`transport`; this service no longer imports AzureTTSService/
GoogleLLMService/PromptBroker or reads Azure/Gemini credentials itself,
only uses the objects it's handed). Zero behavior change from the Wave 8
move itself: same echo suppression, same sample-rate handling, same flag
parsing, same stop-signal polling — only the construction/persistence
plumbing moved to Foundation-tier services matching every other feature's
shape. New narrow ORC-001 waiver (10 constructor dependencies after H4 --
3 Foundation services, 3 bare pipecat service handles, 4 brokers/config)
per CLAUDE.md's Phase 2 Layer-Agent Mapping.

Lives under api/services/orchestrations/voice_conversation/, matching
Review's (api/services/orchestrations/review/) and Ingestion's
(rag/services/orchestrations/ingestion/) Orchestration-tier placement --
moved here from a flat api/services/voice_conversation/ as a same-day
follow-up to this wave, once the flat layout was flagged as an
inconsistency rather than a deliberate exception.

No Validations mixin: no input validation happens at this tier (same as
Review's own file -- see review_service.py's docstring). Exceptions mixin
now exists (voice_conversation_service_exceptions.py,
ConversationOrchestrationServiceExceptions), combined into the concrete
ConversationOrchestrationService in __init__.py -- mirrors Session Lifecycle/
Review's `partial class` merge exactly. One honest caveat this mirroring
does NOT change: unlike Session Lifecycle/Review, there is still no
second, distinct wrapper-tier exception class here -- _try_catch catches
raw stdlib KeyError/OSError and wraps them straight into
VoiceConversationConfigError/VoiceConversationPipelineError, the same two
flat leaves this feature has always had (still inheriting ApiError
directly, no intermediate class). What moved is the *mechanical* pattern
(_try_catch delegate method, _create_and_log_*_exception helpers, an
injected LoggingBroker) — not a new exception hierarchy that didn't exist
before.

_try_catch's scope is deliberately narrower than Session Lifecycle/
Review's: it wraps only _setup() (everything through
`runner.add_workers(worker)`), not the live conversation loop
(`runner.run()`) or its finally-block cleanup — same scope the old inline
try/except covered before this move, preserved on purpose rather than
silently expanded.

Everything else DOES follow the pattern: i_voice_conversation_service.py
(VoiceConversationService Protocol, mirrors Session Lifecycle/Review's
interface files), and the two pipecat frame-filter helper classes
(_MicGate, _TurnStateObserver) live in their own files
(_mic_gate.py, _turn_state_observer.py) rather than bundled into this one
— this file now holds only _ConversationOrchestrationServiceBase and the small
module-level flag-parsing functions it directly uses.
"""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import TTSSpeakFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.processors.aggregators.llm_text_processor import LLMTextProcessor
from pipecat.processors.audio.audio_buffer_processor import AudioBufferProcessor
from pipecat.processors.filters.function_filter import FunctionFilter
from pipecat.utils.text.pattern_pair_aggregator import MatchAction, PatternMatch, PatternPairAggregator
from pipecat.services.azure.tts import AzureTTSService
from pipecat.services.google.llm import GoogleLLMService
from pipecat.transports.local.audio import LocalAudioTransport
from pipecat.turns.user_mute import AlwaysUserMuteStrategy
from pipecat.workers.runner import WorkerRunner

from api.brokers.configuration import ConfigurationBroker, EnvConfigurationBroker
from api.brokers.logging import LoggingBroker
from api.brokers.prompt import FilePromptBroker, PromptBroker
from api.brokers.session_log import SessionLogBroker
from api.brokers.stt import SttBroker
from api.data.spanish_variants import SpanishVariant, get_variant, is_dialect_legit
from api.models.foundations.flag import Flag
from api.models.foundations.flag.exceptions import FlagDependencyException, FlagServiceException
from api.models.foundations.session_log.exceptions import (
    SessionLogDependencyException,
    SessionLogServiceException,
)
from api.models.foundations.live_transcript.exceptions import (
    LiveTranscriptDependencyException,
    LiveTranscriptServiceException,
)
from api.models.orchestrations.voice_conversation.exceptions import VoiceConversationPipelineError
from api.models.foundations.session_log_entry.exceptions import (
    SessionLogEntryDependencyException,
    SessionLogEntryServiceException,
    SessionLogEntryValidationException,
)
from api.models.foundations.session_log_entry.session_log_entry import SessionLogEntry
from api.services.foundations.flag import IFlagService
from api.services.foundations.learner_profile import ILearnerProfileService
from api.services.foundations.session_log_entry import ISessionLogEntryService
from api.services.foundations.live_transcript import ILiveTranscriptService
from api.services.foundations.session_log import ISessionLogService
from api.services.orchestrations.session_audio_recording import ISessionAudioRecordingService
from api.services.processings.learner_profile import ILearnerProfileProcessingService
from api.services.processings.persona import IPersonaProcessingService
from api.services.orchestrations.voice_conversation._mic_gate import _MicGate
from api.services.orchestrations.voice_conversation._pressure import get_pressure_level
from api.services.orchestrations.voice_conversation._turn_state_observer import _TurnStateObserver
from api.services.orchestrations.voice_conversation.i_voice_conversation_service import VoiceConversationService
from api.services.orchestrations.voice_conversation.voice_conversation_service_exceptions import (
    ConversationOrchestrationServiceExceptions,
)
from rag.services.foundations.generation import IGenerationService

REPO_ROOT = Path(__file__).resolve().parents[3]

FLAG_START = "<flag>"
FLAG_END = "</flag>"
FLAG_TYPE = "error_flag"
FLAG_KEYS = ("said", "corrected", "category")
# "channel" is validated separately (defaulted, not required) -- flag
# emission is prompt-compliance-only (see the ponytail note below), and an
# older/non-compliant model turn that omits it shouldn't drop the whole flag.
FLAG_CHANNELS = ("grammar", "lexis", "pronunciation", "orthography")


# ponytail: flag emission is prompt-compliance-only, no API-level guarantee.
# Verified via text-mode probe (Phase 1, 2026-08-28): "Ayer yo como una
# manzana" got silently corrected in the spoken reply ("ayer comí una
# manzana") but no <flag> was emitted for the preterite-conjugation error —
# the model noticed but skipped the flag step. Accepted per scope doc's "log
# everything flagged, unfiltered" — under-flagging is a known gap, not a bug
# to chase. Upgrade path if manual review shows this misses too much:
# response_schema via settings.extra, trading away streamed TTS latency.


def _message_text(content) -> str:
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


def parse_flag(content: str, logging_broker: LoggingBroker) -> Optional[dict]:
    """Parse one <flag> block's JSON payload. Returns None (and warns via
    `logging_broker`) if the model emitted something unparseable — a dropped
    flag is fine, a crashed voice loop is not.

    `logging_broker` is a plain parameter (not `self._logging_broker`) --
    this is a free function, not a method; its one caller (on_error_flag,
    nested inside _setup()) passes the instance's injected broker through."""
    try:
        flag = json.loads(content)
    except json.JSONDecodeError:
        logging_broker.log_warning("Dropped unparseable error flag: %r", content)
        return None
    if not isinstance(flag, dict) or not all(isinstance(flag.get(key), str) for key in FLAG_KEYS):
        logging_broker.log_warning("Dropped malformed error flag: %r", content)
        return None
    channel = flag.get("channel")
    if channel not in FLAG_CHANNELS:
        channel = "grammar"
    return {**{key: flag[key] for key in FLAG_KEYS}, "channel": channel}


def _truncate_at_boundary(text: str, max_chars: int) -> str:
    """Truncate `text` to at most `max_chars`, preferring a clean break over
    a mid-word/mid-sentence cut: the last sentence end (". ", "! ", "? ")
    within the limit if one exists past roughly half of it, else the last
    whitespace, else a hard cut."""
    if len(text) <= max_chars:
        return text
    window = text[:max_chars]
    best_end = max((window.rfind(t) for t in (". ", "! ", "? ")), default=-1)
    if best_end >= max_chars // 2:
        return window[: best_end + 1].rstrip()
    space_idx = window.rfind(" ")
    if space_idx > 0:
        return window[:space_idx].rstrip()
    return window


def _record_flag(
    session_flags: List[Flag],
    parsed: dict,
    logging_broker: LoggingBroker,
    variant: SpanishVariant = get_variant(None),
) -> None:
    """Apply one parsed flag to the running session_flags list — the single
    point A7 (dedupe) and B3 (channel suppression) both act at, so every
    future flag writer inherits both for free instead of re-implementing
    them per caller.

    Orthography-channel flags are dropped outright: a spoken session can't
    produce a legitimate one (there's no writing to get wrong) until E2
    (dictation-back) exists. Flags whose `said` uses a form legit in the
    session's regional `variant` (D2) are dropped the same way. A repeat of the same (category, said, corrected)
    within this session increments the existing Flag's occurrence_count
    instead of appending a new row.
    """
    if parsed["channel"] == "orthography":
        logging_broker.log_info(f"Suppressed orthography-channel flag (spoken session): {parsed['said']!r}")
        return
    # D2: a form that is correct in the chosen regional variety (voseo,
    # vosotros, ahorita...) is not an error -- same guard point as B3 above.
    if is_dialect_legit(parsed["said"], variant):
        logging_broker.log_info(f"Suppressed dialect-legit flag ({variant.key}): {parsed['said']!r}")
        return
    for existing in session_flags:
        if (existing.category, existing.said, existing.corrected) == (
            parsed["category"],
            parsed["said"],
            parsed["corrected"],
        ):
            existing.occurrence_count += 1
            return
    flag = Flag(
        id=uuid.uuid4().hex,
        said=parsed["said"],
        corrected=parsed["corrected"],
        category=parsed["category"],
        channel=parsed["channel"],
        timestamp=datetime.now(),
    )
    session_flags.append(flag)
    logging_broker.log_info(f"FLAG {flag.category}: {flag.said!r} -> {flag.corrected!r}")


class ConversationOrchestrationService(ConversationOrchestrationServiceExceptions, VoiceConversationService):
    """Owns the live voice conversation — Pipecat pipeline construction,
    error-flag capture, and periodic persistence.

    transport/tts/llm are pipecat's own service objects, this feature's
    Broker layer (per the architecture decision record — not re-wrapped),
    built once at the composition root (api/exposers/voice_conversation.py)
    and injected here (audit H4) -- this service never reads Azure/Gemini
    credentials or the system prompt itself. STT is wrapped (SttBroker)
    because of its fragile private-API override, and injected here directly
    -- W3 of the architecture conformance audit deleted the pass-through
    SttService that used to sit in front of it, and this Orchestration
    service already takes LoggingBroker/ConfigurationBroker directly, so a
    direct broker dependency is the established shape. SessionLogBroker (for
    the turn-state signal only) is injected directly for the same reason.
    FlagService, SessionLogService, LiveTranscriptService, and
    SessionLogEntryService are the Foundation-tier dependencies.

    SessionLogEntryService (roadmap C1/C3) is written here rather than from
    Session Lifecycle's /start and /stop because this is the only component
    that knows both ends of the real conversation: /start returns as soon as
    the subprocess spawns, ~16s before the pipeline is warm, and the exact
    per-session flag count only exists in this service's `session_flags`
    list. Reading it back out of flags.json from the Flask process would
    race the subprocess's own final flush. Both writes are guarded the same
    way the three cleanup writes below are -- a session_log failure must
    never take down a live conversation.

    run() delegates its setup phase to a private _setup() method through
    _try_catch (defined in the Exceptions mixin), mirroring Session
    Lifecycle/Review's `public method -> _try_catch(self._private_method)`
    shape.
    """

    def __init__(
        self,
        stt_broker: SttBroker,
        transport: LocalAudioTransport,
        tts: AzureTTSService,
        llm: GoogleLLMService,
        session_log_service: ISessionLogService,
        live_transcript_service: ILiveTranscriptService,
        flag_service: IFlagService,
        session_log_broker: SessionLogBroker,
        session_log_entry_service: ISessionLogEntryService,
        generation_service: IGenerationService,
        learner_profile_processing_service: ILearnerProfileProcessingService,
        learner_profile_service: ILearnerProfileService,
        *,
        logging_broker: LoggingBroker,
        configuration_broker: ConfigurationBroker = EnvConfigurationBroker(),
        persona_processing_service: Optional[IPersonaProcessingService] = None,
        prompt_broker: PromptBroker = FilePromptBroker(),
        session_audio_recording_service: Optional[ISessionAudioRecordingService] = None,
    ) -> None:
        self._stt_broker = stt_broker
        self._transport = transport
        self._tts = tts
        self._llm = llm
        self._session_log_service = session_log_service
        self._live_transcript_service = live_transcript_service
        self._flag_service = flag_service
        self._session_log_broker = session_log_broker
        self._session_log_entry_service = session_log_entry_service
        # Roadmap A6 -- _estimate_and_persist_cefr_level()'s three
        # dependencies: the rag-side estimate call, and get-or-create +
        # write on the api-side learner_profile singleton.
        self._generation_service = generation_service
        self._learner_profile_processing_service = learner_profile_processing_service
        self._learner_profile_service = learner_profile_service
        # Mirrors the LoggingBroker constructor parameter on
        # ConversationSessionService/_ReviewOrchestrationServiceBase -- _create_and_log_*
        # methods (Exceptions mixin) log through it before raising.
        self._logging_broker = logging_broker
        self._configuration_broker = configuration_broker
        # Persona memory write (teardown only); None = feature not wired.
        self._persona_processing_service = persona_processing_service
        self._prompt_broker = prompt_broker
        # E3 opt-in audio capture: None (or AUDIO_RECORD_ENABLED off) leaves the
        # pipeline exactly as it was. `_recorded_audio` is filled by the audio
        # buffer's on_audio_data handler when the pipeline stops.
        self._session_audio_recording_service = session_audio_recording_service
        self._recorded_audio: Optional[Tuple[bytes, int, int]] = None
        self._setup_timed_out = False

    async def run(self) -> None:
        runner, context, session_flags = await self._try_catch(self._setup)

        # Start background task to write live transcript. Reference kept as a
        # local (alive for run()'s lifetime, same as the pipeline) — an
        # unreferenced task risks being garbage-collected mid-execution.
        live_transcript_task = asyncio.create_task(self._write_live_transcript(context, session_flags))
        stop_watch_task = asyncio.create_task(self._watch_for_stop_signal(runner))

        # ponytail: a stop signal arriving before this point (during audio device
        # /pipeline setup, a few seconds) skips the finally below entirely —
        # verified via direct testing in Phase 1. Narrow window, unlikely in real
        # usage (start, talk, then stop) — accepted rather than wrapping all of
        # run()'s setup in try/finally too, which risks touching already-verified
        # code for a startup race a real user is unlikely to hit.
        self._logging_broker.log_info("Voice loop starting — talk into your mic. Ctrl+C to stop.")
        # Roadmap C1/C3. Opened here, not at /start: the subprocess spawns
        # ~16s before the pipeline is warm (see ConversationSessionService's
        # SESSION_READY_WARMUP_SECONDS), and a speaking-hours meter that
        # counts warm-up is wrong. Guarded like every other persistence
        # write in this method -- a session_log failure logs and the
        # conversation continues, it just won't appear in the meter.
        session_log_entry = self._begin_session_log_entry()
        try:
            await runner.run()
        finally:
            live_transcript_task.cancel()
            stop_watch_task.cancel()
            turns = self._extract_turns(context)
            # Each of the four cleanup writes below is guarded separately:
            # they are independent, and before W3 a failure in an earlier one
            # aborted the whole block and lost the later ones' data.
            try:
                log_path = self._session_log_service.save(turns, session_flags)
                if log_path:
                    self._logging_broker.log_info(f"Session log saved to {log_path}")
            except (SessionLogDependencyException, SessionLogServiceException) as e:
                self._logging_broker.log_error(e)
            try:
                self._flag_service.save_flags(session_flags)
            except (FlagDependencyException, FlagServiceException) as e:
                self._logging_broker.log_error(e)
            # The turn-state write is a UI indicator, not data, so it goes
            # last and swallows its own failure. It used to run first here,
            # unguarded -- an OSError from it aborted the rest of this block
            # and lost both the session log and the flags with it (W3 of the
            # architecture conformance audit).
            try:
                self._session_log_broker.write_turn_state("idle")
            except OSError as e:
                self._logging_broker.log_error(e)
            self._end_session_log_entry(session_log_entry, len(session_flags))
            self._save_session_audio(session_log_entry)
            # Roadmap A6: last in the cleanup block, after every data-
            # critical write above -- an estimate is a nice-to-have signal
            # for D6's difficulty dial, not something worth losing a
            # graceful /stop over if the LLM or DB is unavailable.
            self._estimate_and_persist_cefr_level()
            self._update_persona_memory()

        if self._setup_timed_out:
            raise VoiceConversationPipelineError(
                "Pipeline setup timed out after 60s (a processor blocked while "
                "connecting -- mic/speaker device busy, a hung Azure Speech "
                "connection, or Windows AV scanning fresh native DLLs on a cold "
                "start). No conversation started."
            )

    def _begin_session_log_entry(self) -> Optional[SessionLogEntry]:
        """Open the `session_log` row for this session (roadmap C1/C3).

        Returns None -- and logs -- if the write fails, so a DB that's down
        costs the speaking-hours meter one session rather than costing the
        user a conversation. `_end_session_log_entry` no-ops on None.
        """
        try:
            return self._session_log_entry_service.create_session_log_entry(
                datetime.now(), self._configuration_broker.get("SESSION_SCENARIO_SLUG")
            )
        except (
            SessionLogEntryValidationException,
            SessionLogEntryDependencyException,
            SessionLogEntryServiceException,
        ) as e:
            self._logging_broker.log_error(e)
            return None

    def _end_session_log_entry(self, entry: Optional[SessionLogEntry], flag_count: int) -> None:
        """Close the `session_log` row with its end time and flag count.

        `flag_count` is `len(session_flags)` -- the in-memory list this
        service built as the conversation ran. Deliberately not re-read from
        flags.json: that file is rewritten by this same cleanup block, so
        reading it back would race our own write.

        ponytail: a SIGKILLed subprocess never reaches here, leaving
        ended_at NULL. Both Progress aggregates skip those rows rather than
        guess -- see ProgressOrchestrationService. Upgrade path if that ever
        loses too much data: have the periodic flag-persistence loop
        heartbeat ended_at too.
        """
        if entry is None:
            return
        try:
            self._session_log_entry_service.complete_session_log_entry(entry.id, datetime.now(), flag_count)
        except (
            SessionLogEntryValidationException,
            SessionLogEntryDependencyException,
            SessionLogEntryServiceException,
        ) as e:
            self._logging_broker.log_error(e)

    def _save_session_audio(self, entry: Optional[SessionLogEntry]) -> None:
        """Roadmap E3: best-effort write of the captured session audio (WAV +
        session_audio row). No-ops unless recording was enabled, the audio
        buffer produced data, and the session_log row exists. Broad except by
        design, same as the CEFR/persona teardown steps: audio is a
        nice-to-have and must never break teardown."""
        if entry is None or self._recorded_audio is None or self._session_audio_recording_service is None:
            return
        try:
            pcm, sample_rate, num_channels = self._recorded_audio
            self._session_audio_recording_service.save_recording(entry.id, pcm, sample_rate, num_channels)
            self._logging_broker.log_info(f"Session audio saved for session {entry.id}")
        except Exception as e:  # noqa: BLE001 -- degrade, never crash teardown
            self._logging_broker.log_warning("Session audio save failed (%s): %s", entry.id, e)

    def _estimate_and_persist_cefr_level(self) -> None:
        """Roadmap A6: best-effort CEFR estimate from this session's full
        transcript, persisted to the learner_profile singleton.

        ponytail: called synchronously (not asyncio.create_task), same as
        every other call in this method's caller (run()'s finally block) --
        estimate_cefr_level()/update_learner_profile() are already
        synchronous, blocking calls in this codebase (no asyncio anywhere in
        the GenerationService/LearnerProfile stack), so wrapping a sync call
        in a task wouldn't make it non-blocking; it would only risk it never
        completing before this subprocess exits (asyncio.run() tears down
        pending tasks with the loop once run() returns). A real non-blocking
        version needs a thread/executor, which is over-engineering for one
        best-effort call in a single-user CLI subprocess. Upgrade path if
        teardown latency ever matters: run this in a thread via
        loop.run_in_executor() and await it here (still before run()
        returns, just off the main thread while it waits).

        Broad except by design (per this method's own spec, not this file's
        usual narrow-catch style elsewhere): every failure mode here --
        broker down, DB down, an unparseable LLM answer already handled
        inside estimate_cefr_level() -- must be equally harmless, since this
        is a nice-to-have signal for D6's difficulty dial, not session data.
        """
        try:
            transcript_text = self._live_transcript_service.read_full_text()
            if not transcript_text:
                return
            level = self._generation_service.estimate_cefr_level(transcript_text)
            if level is None:
                return
            # Matches ReviewOrchestrationService.record_practice()'s own
            # ensure_profile() call: single-user app, same config key, so a
            # profile created here or there converges on the same default.
            default_level = self._configuration_broker.get("DEFAULT_PROFICIENCY_LEVEL", "beginner")
            profile = self._learner_profile_processing_service.ensure_profile(default_level)
            self._learner_profile_service.update_learner_profile(profile.id, cefr_estimate=level)
            self._logging_broker.log_info(f"CEFR estimate for this session: {level}")
        except Exception as e:
            self._logging_broker.log_error(e)

    def _update_persona_memory(self) -> None:
        """Best-effort rolling persona memory: merge the persona's existing
        memory with this session's transcript via one LLM call, then persist.
        Teardown only (never during the live conversation). No persona set,
        no processing service wired, or an empty transcript skips; any failure
        logs a warning and is swallowed so flags/session log are never lost."""
        slug = self._configuration_broker.get("SESSION_PERSONA")
        if not slug or self._persona_processing_service is None:
            return
        try:
            transcript_text = self._live_transcript_service.read_full_text()
            if not transcript_text:
                return
            max_chars = int(self._configuration_broker.get("PERSONA_MEMORY_MAX_CHARS", "600"))
            persona = self._persona_processing_service.ensure_persona(slug)
            prompt = self._prompt_broker.get_persona_memory_prompt().format(
                memory=persona.memory or "(none)", transcript=transcript_text, max_chars=max_chars
            )
            summary = self._generation_service.generate_text(prompt)
            if not summary:
                return
            self._persona_processing_service.update_memory(slug, _truncate_at_boundary(summary, max_chars))
            self._logging_broker.log_info(f"Persona memory updated: {slug}")
        except Exception as e:  # noqa: BLE001 -- degrade, never crash teardown
            self._logging_broker.log_warning("Persona memory update failed (%s): %s", slug, e)

    async def _setup(self) -> Tuple[WorkerRunner, LLMContext, List[Flag]]:
        """Construct the pipeline and start it running. Returns (runner,
        context, session_flags) for run() to hand to the conversation loop
        and its cleanup. Routed through _try_catch (Exceptions mixin) --
        the only phase this feature wraps, same scope the old inline
        try/except covered before this move."""
        audio_out_sample_rate = int(self._configuration_broker.get("AUDIO_OUT_SAMPLE_RATE", "24000"))
        # ponytail: hardware calibration knob, not a code fix. Silero VAD's
        # stock default (0.2s) doesn't survive background noise -- brief
        # noise spikes above the confidence threshold keep resetting the
        # 0.2s silence window, so "user stopped speaking" never fires and
        # the bot never responds (confirmed against a real session log,
        # 2026-09-03: multiple consecutive user turns with no assistant
        # reply between them). 0.5s is a starting point, not a measured
        # value -- retune against your own mic/room via VAD_STOP_SECS if
        # turns still hang, or if legitimate mid-sentence pauses start
        # getting cut off.
        vad_stop_secs = float(self._configuration_broker.get("VAD_STOP_SECS", "0.5"))
        # ponytail: same hardware-calibration category as VAD_STOP_SECS above.
        # Silero VAD's stock confidence threshold (0.7) let background noise
        # (fan, hum, room noise) false-trigger "user speaking" in the
        # 2026-09-17 hardware test (checklist item #3). Raise via
        # VAD_CONFIDENCE if noise still triggers false starts, or lower it if
        # quiet speech onset starts getting missed.
        vad_confidence = float(self._configuration_broker.get("VAD_CONFIDENCE", "0.7"))

        # D5 pressure dial -- idle-rescue timing only. VAD_STOP_SECS/
        # VAD_CONFIDENCE above stay hardware-calibration-only, never
        # pressure-driven (see _pressure.py's module docstring).
        pressure = get_pressure_level(self._configuration_broker.get("SESSION_PRESSURE"))
        # D2 regional variant -- drives live-flag suppression here; the voice
        # and prompt side is resolved in the composition root.
        variant = get_variant(self._configuration_broker.get("SESSION_VARIANT"))

        stt = self._stt_broker.create()

        context = LLMContext()
        user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
            context,
            # AlwaysUserMuteStrategy drops user audio/transcription frames while the
            # bot is speaking. Without it, LocalAudioTransport has no acoustic echo
            # cancellation, so the mic hears the bot's own voice through the
            # speakers, Azure STT transcribes it, and the bot ends up replying to
            # itself in a loop.
            user_params=LLMUserAggregatorParams(
                vad_analyzer=SileroVADAnalyzer(
                    params=VADParams(stop_secs=vad_stop_secs, confidence=vad_confidence)
                ),
                user_mute_strategies=[AlwaysUserMuteStrategy()],
                user_idle_timeout=pressure.user_idle_timeout,
            ),
        )

        # Rescue-when-stalled: fires only when user_idle_timeout > 0 (push
        # level sets it to 0, which disables pipecat's idle event entirely --
        # see LLMUserAggregatorParams' docstring -- so this handler is simply
        # never called at push level, by design).
        if pressure.rescue_line:
            @user_aggregator.event_handler("on_user_turn_idle")
            async def on_user_turn_idle(aggregator) -> None:
                await aggregator.push_frame(TTSSpeakFrame(pressure.rescue_line))

        session_flags: List[Flag] = []

        flag_aggregator = PatternPairAggregator()
        flag_aggregator.add_pattern(
            type=FLAG_TYPE,
            start_pattern=FLAG_START,
            end_pattern=FLAG_END,
            action=MatchAction.REMOVE,
        )

        async def on_error_flag(match: PatternMatch) -> None:
            parsed = parse_flag(match.text, self._logging_broker)
            if parsed is None:
                return
            _record_flag(session_flags, parsed, self._logging_broker, variant)

        flag_aggregator.on_pattern_match(FLAG_TYPE, on_error_flag)

        # Initialize live transcript file for Review Mode / later SSE
        self._live_transcript_service.clear()
        self._session_log_broker.write_turn_state("listening")

        # Voice Conversation's own stop-signal file is out of the file-broker
        # scope (Stt/SessionLog/Prompt) -- single-purpose, already simple,
        # not worth a 4th broker. Stashed on self (not a local) so
        # _watch_for_stop_signal, a separate method run as a background
        # task, reads the same path _setup() resolved.
        self._stop_signal_file_path = Path(
            self._configuration_broker.get("STOP_SIGNAL_FILE_PATH", str(REPO_ROOT / "data" / "stop_signal"))
        )

        # Clear any stale stop-flag file left by a prior hard-killed run —
        # otherwise this run would see it and end immediately.
        self._stop_signal_file_path.unlink(missing_ok=True)

        processors = [
            self._transport.input(),
            FunctionFilter(filter=_MicGate(), filter_system_frames=True),
            FunctionFilter(
                filter=_TurnStateObserver(self._session_log_broker), filter_system_frames=True
            ),
            stt,
            user_aggregator,
            self._llm,
            LLMTextProcessor(text_aggregator=flag_aggregator),
            self._tts,
            self._transport.output(),
            assistant_aggregator,
        ]
        audio_buffer = self._build_audio_buffer()
        if audio_buffer is not None:
            # After transport.output() (pipecat's documented spot) so it sees
            # both the mic frames and the bot's output audio.
            processors.insert(processors.index(assistant_aggregator), audio_buffer)
        pipeline = Pipeline(processors)

        # Gemini's own retry (retry_on_timeout=True, set at construction in
        # api/exposers/voice_conversation.py) fires once; if the retried call
        # also stalls, pipecat gives up silently -- no spoken reply, no
        # context entry, conversation just hangs on "thinking" until the user
        # gives up and hits /stop. This speaks a fallback line and lets the
        # user try again instead of hanging indefinitely.
        @self._llm.event_handler("on_completion_timeout")
        async def on_completion_timeout(llm: GoogleLLMService) -> None:
            await llm.push_frame(TTSSpeakFrame("Sorry, I lost my train of thought. Could you say that again?"))

        # ponytail: cold Windows start (AV scanning fresh native DLLs: Azure Speech
        # SDK, ONNX runtime, scikit-learn via NLTK warm-up) can blow the default
        # 20s setup window; bump it rather than chase per-processor timing.
        #
        # AUDIO_OUT_SAMPLE_RATE should match your output device's native rate
        # (query via PyAudio's get_default_output_device_info) — MME doesn't
        # reliably resample, so a mismatch plays back sped up and cut short.
        worker = PipelineWorker(
            pipeline,
            params=PipelineParams(audio_out_sample_rate=audio_out_sample_rate),
            setup_timeout_secs=60.0,
        )

        # A setup timeout makes worker.run() clean up and return normally --
        # no exception, nothing to catch around runner.run() below. Left
        # unhandled, WorkerRunner.run()'s default auto_end=True then sees a
        # "finished" root worker and returns normally too, so the subprocess
        # exits 0: indistinguishable from a real graceful stop, even though no
        # conversation ever started. Flag it as instance state (run() checks
        # self._setup_timed_out after runner.run() finishes and cleanup has
        # run) rather than raising here -- raising here would surface as a
        # generic wrapped exception one step too early, before run()'s own
        # more specific "setup timed out" message.
        @worker.event_handler("on_setup_timeout")
        async def on_setup_timeout(worker):
            self._setup_timed_out = True

        runner = WorkerRunner()
        await runner.add_workers(worker)

        return runner, context, session_flags

    def _build_audio_buffer(self) -> Optional[AudioBufferProcessor]:
        """E3: an AudioBufferProcessor when AUDIO_RECORD_ENABLED is on and a
        recording service is wired, else None (pipeline unchanged). Mono at the
        pipeline's audio_out_sample_rate (source rate; no extra resample).
        buffer_size=0 -> on_audio_data fires once, with the whole session, when
        the pipeline stops -- held in memory until teardown writes it.
        ponytail: ~3MB/min in RAM; chunked streaming to disk if long sessions matter."""
        enabled = str(self._configuration_broker.get("AUDIO_RECORD_ENABLED", "0")).strip().lower()
        if self._session_audio_recording_service is None or enabled not in ("1", "true", "yes", "on"):
            return None
        audio_buffer = AudioBufferProcessor(num_channels=1, auto_start_recording=True)

        @audio_buffer.event_handler("on_audio_data")
        async def on_audio_data(_buffer, audio: bytes, sample_rate: int, num_channels: int) -> None:
            self._recorded_audio = (audio, sample_rate, num_channels)

        return audio_buffer

    @staticmethod
    def _extract_turns(context: LLMContext) -> List[str]:
        """Flatten LLMContext's user/assistant messages into "[role] text"
        lines, for both the end-of-session log and the live transcript."""
        return [
            f"[{message['role']}] {_message_text(message['content'])}"
            for message in context.messages
            if isinstance(message, dict) and message["role"] in ("user", "assistant")
        ]

    async def _watch_for_stop_signal(self, runner: WorkerRunner) -> None:
        """Poll for BotProcessBroker's stop-flag file and end the pipeline
        gracefully when it appears.

        Replaces a Windows CTRL_BREAK_EVENT/SIGBREAK port that looked correct
        but wasn't: confirmed via isolated repro (2026-08-29, no pipecat
        involved) that a parent process programmatically signaling a child it
        spawned doesn't reliably raise KeyboardInterrupt in that child on
        Windows/Python 3 — see api/brokers/bot_process/bot_process_broker.py's
        module docstring. A polled file has no such platform dependency."""
        while True:
            await asyncio.sleep(1.0)
            if self._stop_signal_file_path.exists():
                self._stop_signal_file_path.unlink(missing_ok=True)
                await runner.end("stop requested")
                return

    async def _write_live_transcript(self, context: LLMContext, flags: List[Flag]) -> None:
        """Background task that periodically appends new conversation turns to a
        live JSONL transcript file, and re-saves flags via FlagService, for
        Review Mode.

        Re-saving flags here (not just in run()'s finally block) matters: if
        a stop request (via the stop-flag file) can't end the pipeline within
        the Service's graceful-timeout window, it escalates to terminate()/
        kill(), skipping the finally block entirely. Saving flags every
        second here means Review Mode data survives that even when a
        graceful shutdown doesn't."""
        written_turn_count = 0
        while True:
            await asyncio.sleep(1.0)
            written_turn_count = self._flush_new_turns(context, written_turn_count)
            try:
                self._flag_service.save_flags(flags)
            except (FlagDependencyException, FlagServiceException) as e:
                self._logging_broker.log_error(e)

    def _flush_new_turns(self, context: LLMContext, written_turn_count: int) -> int:
        """Append turns past `written_turn_count` to the live transcript.
        Returns the updated count. Split out of _write_live_transcript so a
        broker failure mid-flush (break below) doesn't also nest inside the
        polling loop's own try/except for the flag re-save."""
        current_turns = [
            msg for msg in context.messages
            if isinstance(msg, dict) and msg["role"] in ("user", "assistant")
        ]
        for turn in current_turns[written_turn_count:]:
            try:
                self._live_transcript_service.append(turn["role"], _message_text(turn["content"]))
            except (LiveTranscriptDependencyException, LiveTranscriptServiceException) as e:
                # Same treatment as the flag save below: this background
                # task must keep polling. Before W3 the broker's OSError
                # escaped raw and killed the task silently, taking the
                # periodic flag re-save with it -- the exact data loss the
                # docstring below says this task exists to prevent.
                self._logging_broker.log_error(e)
                break
            written_turn_count += 1
        return written_turn_count
