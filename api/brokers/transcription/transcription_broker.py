"""AzureTranscriptionBroker -- Azure Speech-backed TranscriptionBroker.

Same PushAudioInputStream / timeout-guard plumbing as
api/brokers/pronunciation_assessment/pronunciation_assessment_broker.py, minus
PronunciationAssessmentConfig -- no reference text here, recognition must stay unbiased
(review-three-pane HANDOFF.md section 3, "Why I did not pick it").
"""

import os
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError

from dotenv import load_dotenv

from azure.cognitiveservices.speech import CancellationDetails, ResultReason, SpeechConfig, SpeechRecognizer
from azure.cognitiveservices.speech.audio import AudioConfig, PushAudioInputStream

from api.models.foundations.transcription.transcription import Transcription

load_dotenv()

LANGUAGE = "es-ES"
# Upper bound on the blocking SDK wait; overridable via env so it is a knob, not a magic number.
TIMEOUT_SECONDS = float(os.environ.get("AZURE_TRANSCRIPTION_TIMEOUT_SECONDS", "45"))
PCM_BYTES_PER_SECOND = 16000 * 2  # 16 kHz, 16-bit mono -- same format PushAudioInputStream defaults to


def _pcm_from_wav(wav_bytes: bytes) -> bytes:
    """Headerless PCM: PushAudioInputStream.write() takes no header (audio.py), so drop the RIFF
    header by locating the `data` chunk instead of assuming a fixed 44-byte header."""
    idx = wav_bytes.find(b"data", 12)
    if idx == -1:
        raise ValueError("WAV has no data chunk")
    start = idx + 8  # skip the "data" tag and 4-byte chunk size
    return wav_bytes[start:]


def _duration_seconds(pcm: bytes) -> float:
    """Deterministic from the PCM length -- works for NoMatch too (Azure gives no duration then)."""
    return len(pcm) / PCM_BYTES_PER_SECOND


def _outcome_from_result(reason: ResultReason, text: str, duration_seconds: float) -> Transcription:
    """Pure mapping of an SDK result's (reason, text) pair to our model -- factored out of
    transcribe() so it's testable without Azure. Canceled/anything else is the caller's job to raise."""
    if reason == ResultReason.RecognizedSpeech:
        return Transcription(text=text, duration_seconds=duration_seconds)
    if reason == ResultReason.NoMatch:
        return Transcription(text="", duration_seconds=duration_seconds)
    raise ValueError(f"_outcome_from_result does not handle {reason}; Canceled/timeout must raise before this call")


class AzureTranscriptionBroker:
    """TranscriptionBroker backed by Azure Speech."""

    def transcribe(self, wav_bytes: bytes) -> Transcription:
        pcm = _pcm_from_wav(wav_bytes)
        duration_seconds = _duration_seconds(pcm)

        speech_config = SpeechConfig(
            subscription=os.environ["AZURE_SPEECH_KEY"],
            region=os.environ["AZURE_SPEECH_REGION"],
        )
        stream = PushAudioInputStream()  # default format: 16 kHz, 16-bit, mono PCM
        stream.write(pcm)
        stream.close()
        recognizer = SpeechRecognizer(
            speech_config=speech_config, audio_config=AudioConfig(stream=stream), language=LANGUAGE
        )

        # ponytail: recognize_once caps at ~30s / one utterance; use continuous recognition if longer
        # audio is ever needed. Wait is bounded via a worker thread so a stuck network call can't hang us.
        pool = ThreadPoolExecutor(max_workers=1)
        try:
            result = pool.submit(recognizer.recognize_once).result(timeout=TIMEOUT_SECONDS)
        except FutureTimeoutError as e:
            raise RuntimeError(f"Azure transcription timed out after {TIMEOUT_SECONDS}s") from e
        finally:
            pool.shutdown(wait=False)

        if result.reason == ResultReason.Canceled:
            details = CancellationDetails(result)
            raise RuntimeError(
                f"Azure transcription canceled: reason={details.reason} "
                f"error_code={details.error_code} details={details.error_details}"
            )
        return _outcome_from_result(result.reason, result.text, duration_seconds)


if __name__ == "__main__":
    # ponytail: assert-based self-check for the pure parts -- no Azure credentials needed, no broker
    # test tier (MEMORY.md). Modeled on api/brokers/pronunciation_result/pronunciation_result_broker.py.

    def _make_wav(pcm: bytes) -> bytes:
        # Minimal RIFF/WAVE header (44 bytes) + PCM payload -- enough for _pcm_from_wav to find "data".
        return b"RIFF" + b"\x00" * 4 + b"WAVEfmt " + b"\x00" * 16 + b"data" + len(pcm).to_bytes(4, "little") + pcm

    silent_pcm = b"\x00\x00" * 16000  # 1 second of 16kHz mono 16-bit silence
    wav = _make_wav(silent_pcm)

    assert _pcm_from_wav(wav) == silent_pcm, "PCM extraction should strip the RIFF header exactly"
    assert _duration_seconds(silent_pcm) == 1.0, "1s of 16kHz/16-bit PCM should compute to 1.0s"
    assert _duration_seconds(b"") == 0.0, "empty PCM should compute to 0.0s"

    recognized = _outcome_from_result(ResultReason.RecognizedSpeech, "hola mundo", 2.5)
    assert recognized == Transcription(text="hola mundo", duration_seconds=2.5), recognized

    no_match = _outcome_from_result(ResultReason.NoMatch, "", 3.1)
    assert no_match == Transcription(text="", duration_seconds=3.1), no_match

    try:
        _outcome_from_result(ResultReason.Canceled, "", 0.0)
        raise AssertionError("Canceled should not be handled by _outcome_from_result")
    except ValueError:
        pass

    print("ok")
