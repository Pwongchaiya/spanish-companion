"""Step 1 voice loop: mic -> Azure STT -> Gemini -> Azure TTS -> speaker.

No error-flagging, no RAG (those are Steps 2-3). Verify this feels
conversational before building anything on top. See spanish-companion-mvp-scope.md
Section 7 (Build Order).
"""

import os
from datetime import datetime
from pathlib import Path

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
    "— those symbols get read aloud literally. Say each Spanish phrase as "
    "its own plain sentence, not tucked inside parentheses or quotes in the "
    "middle of an English sentence."
)


LOG_DIR = Path(__file__).parent / "logs"


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


def save_session_log(context: LLMContext) -> Path | None:
    """Write the session's conversation turns to a timestamped file under
    voice/logs/, for manual review per this step's testing standard (no
    automated transcript checks yet — see CLAUDE.md Testing Standards)."""
    turns = [
        f"[{message['role']}] {_message_text(message['content'])}"
        for message in context.messages
        if message["role"] in ("user", "assistant")
    ]
    if not turns:
        return None

    LOG_DIR.mkdir(exist_ok=True)
    log_path = LOG_DIR / f"{datetime.now():%Y-%m-%d-%H%M%S}.log"
    log_path.write_text("\n".join(turns) + "\n", encoding="utf-8")
    return log_path


async def run() -> None:
    load_dotenv()

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
        region=os.environ["AZURE_SPEECH_REGION"],
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

    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            user_aggregator,
            llm,
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

    logger.info("Voice loop starting — talk into your mic. Ctrl+C to stop.")
    try:
        await runner.run()
    finally:
        log_path = save_session_log(context)
        if log_path:
            logger.info(f"Session log saved to {log_path}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(run())
