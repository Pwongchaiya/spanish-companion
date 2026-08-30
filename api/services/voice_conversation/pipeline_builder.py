"""Pipecat pipeline construction for Conversation Mode.

Builds the transport/STT/TTS/LLM chain, wires echo suppression and
error-flag capture, and starts the WorkerRunner. Split out of
voice_conversation_service.py for single-responsibility: construction is
config/wiring, orchestration (run loop, background tasks, persistence)
stays in ConversationOrchestrator.
"""

import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.processors.aggregators.llm_text_processor import LLMTextProcessor
from pipecat.processors.filters.function_filter import FunctionFilter
from pipecat.utils.text.pattern_pair_aggregator import MatchAction, PatternMatch, PatternPairAggregator
from pipecat.services.azure.stt import AzureSTTService
from pipecat.services.azure.tts import AzureTTSService
from pipecat.services.google.llm import GoogleLLMService
from pipecat.transcriptions.language import Language
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams
from pipecat.turns.user_mute import AlwaysUserMuteStrategy
from pipecat.workers.runner import WorkerRunner

from api.models.flag import Flag
from api.models.voice_conversation.exceptions import (
    VoiceConversationConfigError,
    VoiceConversationPipelineError,
)
from api.services.voice_conversation.flags import FLAG_END, FLAG_START, FLAG_TYPE, parse_flag
from api.services.voice_conversation.mic_gate import _MicGate
from api.services.voice_conversation.pipecat_stt import BilingualAzureSTTService
from api.services.voice_conversation.prompts import SYSTEM_PROMPT

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[3]

# ponytail: same os.getenv-at-import-time pattern as every other Phase 2
# module (load_dotenv() then os.getenv with a string default). data/ matches
# FlagBroker's/PracticeLogBroker's own file location convention, replacing
# Phase 1's voice/logs/ — these are new paths, not a port of the old ones.
TRANSCRIPT_FILE_PATH = Path(os.getenv("TRANSCRIPT_FILE_PATH", str(REPO_ROOT / "data" / "live_transcript.jsonl")))
STOP_SIGNAL_FILE_PATH = Path(os.getenv("STOP_SIGNAL_FILE_PATH", str(REPO_ROOT / "data" / "stop_signal")))


@dataclass
class PipelineBuild:
    """Everything ConversationOrchestrator.run() needs from a built pipeline."""

    runner: WorkerRunner
    context: LLMContext
    session_flags: List[Flag] = field(default_factory=list)


async def build_pipeline() -> PipelineBuild:
    """Construct and start the Pipecat pipeline/worker for one conversation
    session.

    Raises VoiceConversationConfigError on missing env config,
    VoiceConversationPipelineError on audio device/file-system setup
    failure.
    """
    try:
        gemini_model = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
        # Multilingual voice — speaks both the Spanish phrases and the English
        # explanations naturally, instead of an English accent on a Spanish-only voice.
        azure_voice = os.getenv("AZURE_TTS_VOICE", "es-ES-XimenaMultilingualNeural")
        audio_out_sample_rate = int(os.getenv("AUDIO_OUT_SAMPLE_RATE", "24000"))

        transport = LocalAudioTransport(
            LocalAudioTransportParams(audio_in_enabled=True, audio_out_enabled=True)
        )

        stt = BilingualAzureSTTService(
            api_key=os.environ["AZURE_SPEECH_KEY"],
            # Continuous LID requires a SpeechConfig built from an explicit endpoint
            # rather than region= (Microsoft's documented requirement) — this is
            # pipecat's only hook for that, despite the Private-Link-flavored name.
            # URL is the standard real-time STT endpoint for the region, per
            # https://learn.microsoft.com/azure/ai-services/speech-service/get-started-speech-to-text
            # (same endpoint region= builds internally; nothing else changes).
            private_endpoint=(
                f"wss://{os.environ['AZURE_SPEECH_REGION']}.stt.speech.microsoft.com"
                "/speech/recognition/conversation/cognitiveservices/v1"
            ),
            settings=AzureSTTService.Settings(language=Language.ES_ES),
        )

        tts = AzureTTSService(
            api_key=os.environ["AZURE_SPEECH_KEY"],
            region=os.environ["AZURE_SPEECH_REGION"],
            settings=AzureTTSService.Settings(voice=azure_voice, language=Language.ES_ES),
        )

        llm = GoogleLLMService(
            api_key=os.environ["GEMINI_API_KEY"],
            settings=GoogleLLMService.Settings(
                model=gemini_model,
                system_instruction=SYSTEM_PROMPT,
            ),
            # A slow first chunk (network blip, API-side latency) otherwise drops
            # the turn silently with no assistant reply ever recorded — the user
            # just keeps talking into what looks like silence, and each unanswered
            # turn piles onto a growing, non-alternating context that makes the
            # next request slower too. One retry breaks that spiral.
            retry_on_timeout=True,
        )

        context = LLMContext()
        user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
            context,
            # AlwaysUserMuteStrategy drops user audio/transcription frames while the
            # bot is speaking. Without it, LocalAudioTransport has no acoustic echo
            # cancellation, so the mic hears the bot's own voice through the
            # speakers, Azure STT transcribes it, and the bot ends up replying to
            # itself in a loop.
            user_params=LLMUserAggregatorParams(
                vad_analyzer=SileroVADAnalyzer(),
                user_mute_strategies=[AlwaysUserMuteStrategy()],
            ),
        )

        session_flags: List[Flag] = []

        flag_aggregator = PatternPairAggregator()
        flag_aggregator.add_pattern(
            type=FLAG_TYPE,
            start_pattern=FLAG_START,
            end_pattern=FLAG_END,
            action=MatchAction.REMOVE,
        )

        async def on_error_flag(match: PatternMatch) -> None:
            parsed = parse_flag(match.text)
            if parsed is None:
                return
            flag = Flag(
                id=uuid.uuid4().hex,
                said=parsed["said"],
                corrected=parsed["corrected"],
                category=parsed["category"],
                timestamp=datetime.now(),
            )
            session_flags.append(flag)
            logger.info(f"FLAG {flag.category}: {flag.said!r} -> {flag.corrected!r}")

        flag_aggregator.on_pattern_match(FLAG_TYPE, on_error_flag)

        # Initialize live transcript file for Review Mode / later SSE
        TRANSCRIPT_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        TRANSCRIPT_FILE_PATH.write_text("", encoding="utf-8")

        # Clear any stale stop-flag file left by a prior hard-killed run —
        # otherwise this run would see it and end immediately.
        STOP_SIGNAL_FILE_PATH.unlink(missing_ok=True)

        pipeline = Pipeline(
            [
                transport.input(),
                FunctionFilter(filter=_MicGate(), filter_system_frames=True),
                stt,
                user_aggregator,
                llm,
                LLMTextProcessor(text_aggregator=flag_aggregator),
                tts,
                transport.output(),
                assistant_aggregator,
            ]
        )

        # ponytail: cold Windows start (AV scanning fresh native DLLs: Azure Speech
        # SDK, ONNX runtime, scikit-learn via NLTK warm-up) can blow the default
        # 20s setup window; bump it rather than chase per-processor timing.
        #
        # AUDIO_OUT_SAMPLE_RATE should match your output device's native rate
        # (query via PyAudio's get_default_output_device_info) — MME doesn't
        # reliably resample, so a mismatch plays back sped up and cut short.
        # ponytail: known gap — pipecat's setup-timeout path (worker.py's
        # _setup_within_timeout) swallows its own asyncio.wait_for TimeoutError
        # internally and just returns False; add_workers() doesn't wait for
        # setup to finish anyway (schedules worker.run() as a background task
        # and returns after asyncio.sleep(0)). Nothing raises here on timeout,
        # so it can't be caught with a try/except around this call. Catching
        # it for real means hooking `@worker.event_handler("on_setup_timeout")`
        # on the worker below and raising VoiceConversationPipelineError from
        # that handler instead — bigger change than this fix pass covers.
        worker = PipelineWorker(
            pipeline,
            params=PipelineParams(audio_out_sample_rate=audio_out_sample_rate),
            setup_timeout_secs=60.0,
        )
        runner = WorkerRunner()
        await runner.add_workers(worker)

    except KeyError as e:
        raise VoiceConversationConfigError(
            f"Missing required configuration: {e}"
        ) from e
    except OSError as e:
        raise VoiceConversationPipelineError(
            f"Audio device initialization failed: {e}"
        ) from e

    return PipelineBuild(runner=runner, context=context, session_flags=session_flags)
