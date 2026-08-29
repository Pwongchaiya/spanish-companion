"""Step 1 voice loop: mic -> Azure STT -> Gemini -> Azure TTS -> speaker.

No error-flagging, no RAG (those are Steps 2-3). Verify this feels
conversational before building anything on top. See spanish-companion-mvp-scope.md
Section 7 (Build Order).
"""

import asyncio
import json
import os
import signal
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import BotStartedSpeakingFrame, BotStoppedSpeakingFrame, InputAudioRawFrame
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
from pipecat.services.azure.stt import AudioConfig, AudioStreamFormat, AzureSTTService, PushAudioInputStream
from pipecat.services.azure.tts import AzureTTSService
from pipecat.services.google.llm import GoogleLLMService
from pipecat.transcriptions.language import Language
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams
from pipecat.turns.user_mute import AlwaysUserMuteStrategy
from pipecat.workers.runner import WorkerRunner

from azure.cognitiveservices.speech import (
    AutoDetectSourceLanguageConfig,
    PropertyId,
    SpeechRecognizer,
)

BILINGUAL_STT_LANGUAGES = ["es-ES", "en-US"]

FLAG_START = "<flag>"
FLAG_END = "</flag>"
FLAG_TYPE = "error_flag"
FLAG_KEYS = ("said", "corrected", "category")


class BilingualAzureSTTService(AzureSTTService):
    """Azure STT with continuous language identification between Spanish
    and English, so the learner can ask a question in either language
    mid-conversation.

    Pipecat's AzureSTTService only supports one fixed recognition language,
    with no hook for AutoDetectSourceLanguageConfig — so this re-implements
    _connect() to add it. Keep in sync with upstream's _connect() if pipecat
    changes it (pipecat-ai==1.8.1 as of writing).

    Continuous LID re-detects per utterance (not mid-sentence) and adds
    per-utterance detection overhead — a deliberate cost against this
    project's "Conversation Mode stays fast" principle, traded for actually
    understanding English questions.
    """

    async def _connect(self):
        if self._audio_stream:
            return

        try:
            self._speech_config.set_property(
                PropertyId.SpeechServiceConnection_LanguageIdMode, "Continuous"
            )

            stream_format = AudioStreamFormat(samples_per_second=self.sample_rate, channels=1)
            self._audio_stream = PushAudioInputStream(stream_format)
            audio_config = AudioConfig(stream=self._audio_stream)
            auto_detect_config = AutoDetectSourceLanguageConfig(languages=BILINGUAL_STT_LANGUAGES)

            self._speech_recognizer = SpeechRecognizer(
                speech_config=self._speech_config,
                audio_config=audio_config,
                auto_detect_source_language_config=auto_detect_config,
            )
            self._speech_recognizer.recognizing.connect(self._on_handle_recognizing)
            self._speech_recognizer.recognized.connect(self._on_handle_recognized)
            self._speech_recognizer.canceled.connect(self._on_handle_canceled)
            self._speech_recognizer.start_continuous_recognition_async()
        except Exception as e:
            await self.push_error(
                error_msg=f"Uncaught exception during initialization: {e}", exception=e
            )


class _MicGate:
    """Drops mic audio while the bot is speaking.

    LocalAudioTransport has no acoustic echo cancellation, so without this the
    mic hears the bot's own TTS output through the speakers and streams it to
    Azure STT. AlwaysUserMuteStrategy alone doesn't stop that: it filters
    downstream of STT, but Azure's cloud endpointing finalizes a "recognized"
    transcript of the echo the instant TTS audio stops, landing right as that
    mute window closes. Gating here, before STT ever sees the audio, removes
    the echo transcript instead of racing to drop it after the fact.

    Only gates InputAudioRawFrame — everything else passes through untouched.
    Needs filter_system_frames=True on the FunctionFilter wrapping this:
    InputAudioRawFrame is a SystemFrame, and FunctionFilter auto-passes those
    through by default, which otherwise makes this a no-op.
    """

    def __init__(self):
        self._bot_speaking = False

    async def __call__(self, frame) -> bool:
        if isinstance(frame, BotStartedSpeakingFrame):
            self._bot_speaking = True
        elif isinstance(frame, BotStoppedSpeakingFrame):
            self._bot_speaking = False
        if isinstance(frame, InputAudioRawFrame):
            return not self._bot_speaking
        return True


# ponytail: flag emission is prompt-compliance-only, no API-level guarantee.
# Verified via text-mode probe (2026-08-28): "Ayer yo como una manzana" got
# silently corrected in the spoken reply ("ayer comí una manzana") but no
# <flag> was emitted for the preterite-conjugation error — the model noticed
# but skipped the flag step. Accepted per scope doc's "log everything
# flagged, unfiltered" — under-flagging is a known gap, not a bug to chase.
# Upgrade path if manual review shows this misses too much: response_schema
# via settings.extra (see Step 2 plan), trading away streamed TTS latency.
SYSTEM_PROMPT = (
    "You are a warm, friendly bilingual companion helping a native English "
    "speaker learn to speak Spanish, by voice. Walk them through Spanish "
    "phrases conversationally: say a phrase in Spanish, briefly explain what "
    "it means in English, then invite them to try saying it back. Cover one "
    "phrase or idea per turn, not a list. Keep it warm and casual, like a "
    "friend teaching you over coffee, not a formal lesson. Keep responses "
    "short, since this is a real-time spoken conversation.\n\n"
    "This is spoken aloud by a text-to-speech engine, not displayed as text. "
    "Never use markdown, asterisks, quotation marks, or any other formatting "
    "— those symbols get read aloud literally. The voice picks one language "
    "per sentence and reads the whole sentence in it — so a Spanish word or "
    "phrase sharing a sentence with English, in ANY way (comma-spliced, "
    "parenthesized, quoted, or otherwise), gets read aloud with an English "
    "accent instead of Spanish. Every Spanish phrase must be its own "
    "complete, standalone sentence with nothing English in it, and every "
    "English sentence must have nothing Spanish in it. Always write Spanish "
    "with its correct accents and punctuation — é, í, ó, ú, á, ñ, ¿, ¡ — "
    "never drop them (tú, not tu; cómo, not como, when it means how).\n\n"
    "Separately from what you say aloud, watch for mistakes the learner makes "
    "in Spanish — grammar, verb conjugation, gender agreement, or word choice. "
    "When you notice one, append a flag at the very END of your reply, after "
    "everything you say aloud, in exactly this form:\n"
    "<flag>{\"said\": \"what they actually said\", \"corrected\": \"the corrected "
    "Spanish\", \"category\": \"short label\"}</flag>\n"
    "One flag block per mistake; emit several blocks if there were several. "
    "Use short category labels like ser vs estar, preterite vs imperfect, "
    "gender agreement, subjunctive, vocabulary. Emit nothing if there was no "
    "mistake — most turns will have none. Never mention the flag, never read "
    "it aloud, never correct the learner out loud; the flag is silent and is "
    "reviewed after the conversation. Nothing may follow the closing tag."
)


LOG_DIR = Path(__file__).parent / "logs"
LIVE_TRANSCRIPT_PATH = LOG_DIR / "live_transcript.jsonl"


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


def parse_flag(content: str) -> dict[str, str] | None:
    """Parse one <flag> block's JSON payload. Returns None (and warns) if the
    model emitted something unparseable — a dropped flag is fine, a crashed
    voice loop is not."""
    try:
        flag = json.loads(content)
    except json.JSONDecodeError:
        logger.warning(f"Dropped unparseable error flag: {content!r}")
        return None
    if not isinstance(flag, dict) or not all(isinstance(flag.get(key), str) for key in FLAG_KEYS):
        logger.warning(f"Dropped malformed error flag: {content!r}")
        return None
    return {key: flag[key] for key in FLAG_KEYS}


def save_session_log(context: LLMContext, flags: list[dict[str, str]]) -> Path | None:
    """Write the session's conversation turns to a timestamped file under
    voice/logs/, for manual review per this step's testing standard (no
    automated transcript checks yet — see CLAUDE.md Testing Standards)."""
    turns = [
        f"[{message['role']}] {_message_text(message['content'])}"
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
                f"[{flag['category']}] said: \"{flag['said']}\" -> corrected: \"{flag['corrected']}\""
            )

    LOG_DIR.mkdir(exist_ok=True)
    log_path = LOG_DIR / f"{datetime.now():%Y-%m-%d-%H%M%S}.log"
    log_path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")
    return log_path


def save_flags_json(flags: list[dict[str, str]]) -> None:
    """Write the session's flagged errors to a fixed JSON file for Review Mode.

    Always writes, even an empty list — Review Mode always reads this as "the
    most recent session's flags"; skipping the write on a flag-free session
    would leave a stale prior session's errors looking current."""
    LOG_DIR.mkdir(exist_ok=True)
    flags_path = LOG_DIR / "latest_flags.json"
    flags_path.write_text(json.dumps(flags, ensure_ascii=False, indent=2), encoding="utf-8")


async def _write_live_transcript(context: LLMContext, flags: list[dict[str, str]]) -> None:
    """Background task that periodically appends new conversation turns to a live
    JSONL transcript file, and re-saves flags.json, for Review Mode.

    Re-saving flags.json here (not just in run()'s finally block) matters: on
    Windows, a stop request delivered via CTRL_BREAK_EVENT (the Flask UI's
    /stop route) can leave pipecat's pipeline cancellation hanging indefinitely
    once the audio pipeline is fully active (verified: still hadn't completed
    after a 30s wait) — the process ends up hard-killed, skipping the finally
    block entirely. Saving flags every second here means Review Mode data
    survives that even when a graceful shutdown doesn't."""
    written_turn_count = 0
    while True:
        await asyncio.sleep(1.0)
        # Get all current turns (user + assistant messages), using same filter as save_session_log
        current_turns = [
            msg for msg in context.messages
            if isinstance(msg, dict) and msg["role"] in ("user", "assistant")
        ]

        # Append any new turns since last check
        for turn in current_turns[written_turn_count:]:
            line = json.dumps(
                {"role": turn["role"], "text": _message_text(turn["content"])},
                ensure_ascii=False,
            )
            with open(LIVE_TRANSCRIPT_PATH, "a", encoding="utf-8") as f:
                f.write(line + "\n")
            written_turn_count += 1

        save_flags_json(flags)


async def run() -> None:
    load_dotenv()

    # Windows has no default handler for CTRL_BREAK_EVENT (SIGBREAK) — unlike
    # SIGINT/Ctrl+C, which Python auto-converts to KeyboardInterrupt, an
    # unhandled SIGBREAK just kills the process outright, skipping the
    # try/finally below entirely (verified: session log/flags never got
    # written). This lets a parent process (the Flask UI's /stop route)
    # request the same graceful shutdown Ctrl+C already gets interactively.
    if hasattr(signal, "SIGBREAK"):

        def _handle_sigbreak(signum, frame) -> None:
            raise KeyboardInterrupt

        signal.signal(signal.SIGBREAK, _handle_sigbreak)

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

    session_flags: list[dict[str, str]] = []

    flag_aggregator = PatternPairAggregator()
    flag_aggregator.add_pattern(
        type=FLAG_TYPE,
        start_pattern=FLAG_START,
        end_pattern=FLAG_END,
        action=MatchAction.REMOVE,
    )

    async def on_error_flag(match: PatternMatch) -> None:
        flag = parse_flag(match.text)
        if flag is None:
            return
        session_flags.append(flag)
        logger.info(f"FLAG {flag['category']}: {flag['said']!r} -> {flag['corrected']!r}")

    flag_aggregator.on_pattern_match(FLAG_TYPE, on_error_flag)

    # Initialize live transcript file for Review Mode
    LOG_DIR.mkdir(exist_ok=True)
    LIVE_TRANSCRIPT_PATH.write_text("", encoding="utf-8")

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
    worker = PipelineWorker(
        pipeline,
        params=PipelineParams(audio_out_sample_rate=audio_out_sample_rate),
        setup_timeout_secs=60.0,
    )
    runner = WorkerRunner()
    await runner.add_workers(worker)

    # Start background task to write live transcript. Reference kept as a
    # local (alive for run()'s lifetime, same as the pipeline) — an
    # unreferenced task risks being garbage-collected mid-execution.
    live_transcript_task = asyncio.create_task(_write_live_transcript(context, session_flags))

    # ponytail: a stop signal arriving before this point (during audio device
    # /pipeline setup, a few seconds) skips the finally below entirely —
    # verified via direct testing. Narrow window, unlikely in real usage
    # (start, talk, then stop) — accepted rather than wrapping all of run()'s
    # setup in try/finally too, which risks touching already-verified code
    # for a startup race a real user is unlikely to hit.
    logger.info("Voice loop starting — talk into your mic. Ctrl+C to stop.")
    try:
        await runner.run()
    finally:
        log_path = save_session_log(context, session_flags)
        if log_path:
            logger.info(f"Session log saved to {log_path}")
        save_flags_json(session_flags)


if __name__ == "__main__":
    import asyncio

    asyncio.run(run())
