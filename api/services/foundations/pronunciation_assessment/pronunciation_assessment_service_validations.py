"""Validation checks for PronunciationAssessmentService.

Mirrors TtsServiceValidations (api/services/foundations/tts/tts_service_validations.py): every failing
field is batched into one InvalidPronunciationAssessmentRequestException.
"""

from api.models.foundations.pronunciation_assessment.exceptions import (
    InvalidPronunciationAssessmentRequestException,
)

# ponytail: 1 MiB is ~32s of 16 kHz mono 16-bit audio, matching recognize_once's ~30s ceiling in the broker.
MAX_WAV_BYTES = 1_048_576
MAX_REFERENCE_TEXT_LENGTH = 200


class PronunciationAssessmentServiceValidations:
    """Mixin: raises the leaf exception (with every failing field attached) on invalid input."""

    def _validate_on_assess_pronunciation(self, wav_bytes: bytes | None, reference_text: str | None) -> None:
        self._validate(
            (self._is_empty_wav(wav_bytes), "wav_bytes", "WAV audio is required"),
            (self._is_too_large(wav_bytes), "wav_bytes", f"WAV audio must be {MAX_WAV_BYTES} bytes or fewer"),
            (self._is_not_wav(wav_bytes), "wav_bytes", "Audio must be a RIFF/WAVE file"),
            (self._is_blank(reference_text), "reference_text", "Reference text is required"),
            (
                self._is_too_long(reference_text),
                "reference_text",
                f"Reference text must be {MAX_REFERENCE_TEXT_LENGTH} characters or fewer",
            ),
        )

    @staticmethod
    def _is_empty_wav(value: bytes | None) -> bool:
        return not isinstance(value, (bytes, bytearray)) or len(value) == 0

    @staticmethod
    def _is_too_large(value: bytes | None) -> bool:
        return isinstance(value, (bytes, bytearray)) and len(value) > MAX_WAV_BYTES

    @staticmethod
    def _is_not_wav(value: bytes | None) -> bool:
        # Empty/wrong-type is reported by _is_empty_wav; only judge the header of non-empty bytes.
        if not isinstance(value, (bytes, bytearray)) or len(value) == 0:
            return False
        return value[:4] != b"RIFF" or value[8:12] != b"WAVE"

    @staticmethod
    def _is_blank(value: str | None) -> bool:
        return not isinstance(value, str) or not value.strip()

    @staticmethod
    def _is_too_long(value: str | None) -> bool:
        return isinstance(value, str) and len(value) > MAX_REFERENCE_TEXT_LENGTH

    @staticmethod
    def _validate(*rules: tuple[bool, str, str]) -> None:
        exception = InvalidPronunciationAssessmentRequestException()
        for condition, field, message in rules:
            if condition:
                exception.upsert_data_list(field, message)
        exception.throw_if_contains_errors()
