"""AzureSttBroker -- Azure Speech-backed SttBroker.

BilingualAzureSTTService moved here verbatim from
api/services/orchestrations/voice_conversation/voice_conversation_service.py
-- folder move only, no behavior change. See i_stt_broker.py for why STT specifically
gets a broker wrapper while LLM/TTS don't.
"""

import os

from dotenv import load_dotenv

from pipecat.services.azure.stt import AudioConfig, AudioStreamFormat, AzureSTTService, PushAudioInputStream
from pipecat.transcriptions.language import Language

from azure.cognitiveservices.speech import (
    AutoDetectSourceLanguageConfig,
    PropertyId,
    SpeechRecognizer,
)

load_dotenv()

BILINGUAL_STT_LANGUAGES = ["es-ES", "en-US"]


class BilingualAzureSTTService(AzureSTTService):
    """Azure STT with continuous language identification between Spanish
    and English, so the learner can ask a question in either language
    mid-conversation.

    Pipecat's AzureSTTService only supports one fixed recognition language,
    with no hook for AutoDetectSourceLanguageConfig -- so this re-implements
    _connect() to add it. Keep in sync with upstream's _connect() if pipecat
    changes it (pipecat-ai==1.8.1, pinned in requirements.txt for exactly
    this reason).

    Continuous LID re-detects per utterance (not mid-sentence) and adds
    per-utterance detection overhead -- a deliberate cost against this
    project's "Conversation Mode stays fast" principle, traded for actually
    understanding English questions.
    """

    async def _connect(self):
        if self._audio_stream:
            return

        try:
            self._speech_config.set_property(PropertyId.SpeechServiceConnection_LanguageIdMode, "Continuous")

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
            await self.push_error(error_msg=f"Uncaught exception during initialization: {e}", exception=e)


class AzureSttBroker:
    """SttBroker backed by Azure Speech, reading credentials from the
    environment exactly as the Orchestrator did before this move."""

    def create(self) -> AzureSTTService:
        return BilingualAzureSTTService(
            api_key=os.environ["AZURE_SPEECH_KEY"],
            # Continuous LID requires a SpeechConfig built from an explicit endpoint
            # rather than region= (Microsoft's documented requirement) -- this is
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
