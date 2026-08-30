"""Custom Azure STT service with continuous bilingual language ID.

Split out of voice_conversation_service.py for single-responsibility.
Pipecat's own STT/LLM/TTS service objects are this feature's Broker layer
(per the architecture decision record — not re-wrapped).
"""

from azure.cognitiveservices.speech import (
    AutoDetectSourceLanguageConfig,
    PropertyId,
    SpeechRecognizer,
)
from pipecat.services.azure.stt import AudioConfig, AudioStreamFormat, AzureSTTService, PushAudioInputStream

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
