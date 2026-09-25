"""Validation checks for TranscriptionService.

Mirrors PronunciationAssessmentServiceValidations
(api/services/foundations/pronunciation_assessment/pronunciation_assessment_service_validations.py):
every failing field is batched into one InvalidTranscriptionRequestException.
"""

from api.models.foundations.transcription.exceptions import InvalidTranscriptionRequestException

# ponytail: mirrors WAV_HEADER_BYTES in api/exposers/pronunciation.py -- same 44-byte minimal RIFF/WAVE
# header, duplicated (not imported) because a service must not depend on an exposer.
WAV_HEADER_BYTES = 44


class TranscriptionServiceValidations:
    """Mixin: raises the leaf exception (with every failing field attached) on invalid input."""

    def _validate_on_transcribe(self, wav_bytes: bytes | None) -> None:
        self._validate(
            (self._is_too_short(wav_bytes), "wav_bytes", "audio contains no samples"),
            (self._is_not_wav(wav_bytes), "wav_bytes", "audio must be a RIFF/WAVE file"),
        )

    @staticmethod
    def _is_too_short(value: bytes | None) -> bool:
        return not isinstance(value, (bytes, bytearray)) or len(value) <= WAV_HEADER_BYTES

    @staticmethod
    def _is_not_wav(value: bytes | None) -> bool:
        # Too-short/wrong-type is reported by _is_too_short; only judge the header of long-enough bytes.
        if not isinstance(value, (bytes, bytearray)) or len(value) <= WAV_HEADER_BYTES:
            return False
        return value[:4] != b"RIFF" or value[8:12] != b"WAVE"

    @staticmethod
    def _validate(*rules: tuple[bool, str, str]) -> None:
        exception = InvalidTranscriptionRequestException()
        for condition, field, message in rules:
            if condition:
                exception.upsert_data_list(field, message)
        exception.throw_if_contains_errors()


if __name__ == "__main__":
    # ponytail: assert-based self-check for the pure predicates -- no broker/Flask needed, no pytest
    # tier (MEMORY.md: tests land as a later pass). Modeled on transcription_broker.py's __main__.
    v = TranscriptionServiceValidations()

    assert v._is_too_short(None) is True, "None should be too short"
    assert v._is_too_short(b"") is True, "empty bytes should be too short"
    assert v._is_too_short(b"x" * 44) is True, "exactly header-length should be too short"
    assert v._is_too_short(b"x" * 45) is False, "one byte past the header should not be too short"

    ok_wav = b"RIFF" + b"\x00" * 4 + b"WAVEfmt " + b"\x00" * 33
    assert v._is_not_wav(ok_wav) is False, "well-formed RIFF/WAVE header should pass"
    assert v._is_not_wav(b"x" * 45) is True, "non-RIFF bytes should fail"
    assert v._is_not_wav(b"x" * 44) is False, "too-short bytes are _is_too_short's job, not this one"

    print("ok")
