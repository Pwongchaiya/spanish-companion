"""AzureAssessmentBroker -- Azure Speech-backed PronunciationAssessmentBroker.

Same env vars and raw azure-cognitiveservices-speech approach as api/brokers/tts/tts_broker.py
(AZURE_SPEECH_KEY / AZURE_SPEECH_REGION, KeyError if missing; no pipecat, no new dependency).
"""

import os
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from typing import Any

from dotenv import load_dotenv

from azure.cognitiveservices.speech import (
    CancellationDetails,
    PronunciationAssessmentConfig,
    PronunciationAssessmentGradingSystem,
    PronunciationAssessmentGranularity,
    PronunciationAssessmentResult,
    ResultReason,
    SpeechConfig,
    SpeechRecognizer,
)
from azure.cognitiveservices.speech.audio import AudioConfig, PushAudioInputStream

from api.models.foundations.pronunciation_assessment.pronunciation_assessment import (
    PhonemeScore,
    PronunciationAssessment,
    WordScore,
)

load_dotenv()

LANGUAGE = "es-ES"
# Upper bound on the blocking SDK wait; overridable via env so it is a knob, not a magic number.
TIMEOUT_SECONDS = float(os.environ.get("AZURE_PRONUNCIATION_TIMEOUT_SECONDS", "45"))


def _pcm_from_wav(wav_bytes: bytes) -> bytes:
    """Headerless PCM: PushAudioInputStream.write() takes no header (audio.py), so drop the RIFF
    header by locating the `data` chunk instead of assuming a fixed 44-byte header."""
    idx = wav_bytes.find(b"data", 12)
    if idx == -1:
        raise ValueError("WAV has no data chunk")
    start = idx + 8  # skip the "data" tag and 4-byte chunk size
    return wav_bytes[start:]


def parse_assessment(result: Any) -> PronunciationAssessment:
    """Pure conversion of an SDK PronunciationAssessmentResult (or any object with the same attributes)
    into our model. Words/phonemes/per-word scores may be absent -- the SDK leaves the attribute unset."""
    words: list[WordScore] = []
    for w in getattr(result, "words", None) or []:
        phonemes = [
            PhonemeScore(phoneme=p.phoneme, accuracy_score=p.accuracy_score)
            for p in getattr(w, "phonemes", None) or []
        ]
        error_type = getattr(w, "error_type", None)
        words.append(
            WordScore(
                word=w.word,
                accuracy_score=getattr(w, "accuracy_score", None),
                error_type=str(error_type) if error_type is not None else "None",
                phonemes=phonemes,
            )
        )
    scores = {
        name: getattr(result, name, None)
        for name in ("accuracy_score", "fluency_score", "completeness_score", "pronunciation_score")
    }
    if any(v is None for v in scores.values()):
        raise RuntimeError("Azure returned no pronunciation assessment scores")
    return PronunciationAssessment(**scores, prosody_score=getattr(result, "prosody_score", None), words=words)


class AzureAssessmentBroker:
    """PronunciationAssessmentBroker backed by Azure Speech."""

    def assess(self, wav_bytes: bytes, reference_text: str) -> PronunciationAssessment:
        speech_config = SpeechConfig(
            subscription=os.environ["AZURE_SPEECH_KEY"],
            region=os.environ["AZURE_SPEECH_REGION"],
        )
        stream = PushAudioInputStream()  # default format: 16 kHz, 16-bit, mono PCM
        stream.write(_pcm_from_wav(wav_bytes))
        stream.close()
        recognizer = SpeechRecognizer(
            speech_config=speech_config, audio_config=AudioConfig(stream=stream), language=LANGUAGE
        )
        config = PronunciationAssessmentConfig(
            reference_text=reference_text,
            grading_system=PronunciationAssessmentGradingSystem.HundredMark,
            granularity=PronunciationAssessmentGranularity.Phoneme,
            enable_miscue=True,
        )
        try:
            config.enable_prosody_assessment()
        except Exception:  # noqa: BLE001 -- prosody is optional (en-US only); its score is None otherwise
            pass
        config.apply_to(recognizer)

        # ponytail: recognize_once caps at ~30s / one utterance; use continuous recognition if longer
        # audio is ever needed. Wait is bounded via a worker thread so a stuck network call can't hang us.
        pool = ThreadPoolExecutor(max_workers=1)
        try:
            result = pool.submit(recognizer.recognize_once).result(timeout=TIMEOUT_SECONDS)
        except FutureTimeoutError as e:
            raise RuntimeError(f"Azure pronunciation assessment timed out after {TIMEOUT_SECONDS}s") from e
        finally:
            pool.shutdown(wait=False)

        if result.reason == ResultReason.RecognizedSpeech:
            return parse_assessment(PronunciationAssessmentResult(result))
        if result.reason == ResultReason.Canceled:
            details = CancellationDetails(result)
            raise RuntimeError(
                f"Azure pronunciation assessment canceled: reason={details.reason} "
                f"error_code={details.error_code} details={details.error_details}"
            )
        raise RuntimeError(f"Azure pronunciation assessment found no speech: reason={result.reason}")
