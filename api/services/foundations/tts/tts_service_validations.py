"""Validation checks for TtsService.

Mirrors TopicCoveredServiceValidations' batching Validate(...)/Is* helper
pattern (api/services/foundations/topic_covered/
topic_covered_service_validations.py) -- checks batch into one
InvalidTtsRequestException reporting every failing field, instead of
raising on the first bad field. Only one field here (`text`), so both
checks land on it.
"""

from api.models.foundations.tts.exceptions import InvalidTtsRequestException

# ponytail: generous cap for a single word/short phrase drill (B6's
# minimal-pair list tops out well under this) -- raise it if a future
# feature needs longer TTS prompts through this same endpoint.
MAX_TEXT_LENGTH = 200


class TtsServiceValidations:
    """Mixin: raises the leaf exception (with every failing field attached)
    when input doesn't pass checks. See tts_service_exceptions.py for how
    it gets wrapped and logged before leaving the service.
    """

    def _validate_tts_on_synthesize(self, text: str | None) -> None:
        self._validate(
            (self._is_blank(text), "text", "Text is required"),
            (self._is_too_long(text), "text", f"Text must be {MAX_TEXT_LENGTH} characters or fewer"),
        )

    @staticmethod
    def _is_blank(value: str | None) -> bool:
        return not isinstance(value, str) or not value.strip()

    @staticmethod
    def _is_too_long(value: str | None) -> bool:
        return isinstance(value, str) and len(value) > MAX_TEXT_LENGTH

    @staticmethod
    def _validate(*rules: tuple[bool, str, str]) -> None:
        exception = InvalidTtsRequestException()
        for condition, field, message in rules:
            if condition:
                exception.upsert_data_list(field, message)
        exception.throw_if_contains_errors()
