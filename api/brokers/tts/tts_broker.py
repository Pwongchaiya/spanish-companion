"""AzureTtsBroker -- Azure Speech-backed TtsBroker.

Reads the same AZURE_SPEECH_KEY/AZURE_SPEECH_REGION env vars as
api/brokers/stt/stt_broker.py's AzureSttBroker (shared Azure Speech
resource, no new credentials). Uses the raw azure-cognitiveservices-speech
SDK directly rather than pipecat -- pipecat's AzureTTSService is built for
streaming into a running voice pipeline; this is a single blocking
text -> bytes call outside any pipeline, so the plain SDK is the smaller
surface for the same job (ladder rung 3: SDK already installed, no new
dependency, no pipecat wrapper needed).
"""

import os
from xml.sax.saxutils import escape

from dotenv import load_dotenv

from azure.cognitiveservices.speech import (
    ResultReason,
    SpeechConfig,
    SpeechSynthesisOutputFormat,
    SpeechSynthesizer,
)

load_dotenv()

# ponytail: one fixed Spanish (Spain) neural voice, no per-call voice
# selection -- B6 is a listening-discrimination drill over a static word
# list, not a general TTS feature. Add a `voice` param if a future feature
# needs a different voice/locale.
DEFAULT_VOICE_NAME = "es-ES-ElviraNeural"


def _build_ssml(text: str, rate: float, voice: str) -> str:
    return (
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="es-ES">'
        f'<voice name="{voice}"><prosody rate="{rate}">{escape(text)}</prosody></voice></speak>'
    )


class AzureTtsBroker:
    """TtsBroker backed by Azure Speech, reading credentials from the
    environment exactly as AzureSttBroker does."""

    def synthesize(self, text: str, rate: float = 1.0) -> bytes:
        speech_config = SpeechConfig(
            subscription=os.environ["AZURE_SPEECH_KEY"],
            region=os.environ["AZURE_SPEECH_REGION"],
        )
        # AZURE_TTS_VOICE is the same knob the live voice pipeline reads (.env.example).
        speech_config.speech_synthesis_voice_name = os.environ.get("AZURE_TTS_VOICE") or DEFAULT_VOICE_NAME
        # Explicit WAV format -- this is also the SDK default, but pinning
        # it keeps the Content-Type: audio/wav the Exposer sends correct
        # even if the SDK's own default ever changes.
        speech_config.set_speech_synthesis_output_format(SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm)

        # audio_config=None: don't play to a local speaker (there is none on
        # a server), just hand back the encoded bytes via result.audio_data.
        synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=None)
        if rate != 1.0:
            ssml = _build_ssml(text, rate, speech_config.speech_synthesis_voice_name)
            result = synthesizer.speak_ssml_async(ssml).get()
        else:
            result = synthesizer.speak_text_async(text).get()

        if result.reason == ResultReason.SynthesizingAudioCompleted:
            return result.audio_data

        raise RuntimeError(f"Azure TTS synthesis did not complete: reason={result.reason}")


if __name__ == "__main__":
    _ssml = _build_ssml("a & b", 0.6, DEFAULT_VOICE_NAME)
    assert '<prosody rate="0.6">' in _ssml
    assert "a &amp; b" in _ssml
    print("ok")
