"""Validation checks for PronunciationResultService.

Same batched Validate(...)/Is* predicate pattern as
SessionLogEntryServiceValidations: every failing field is reported in one
InvalidPronunciationResultException. A None result is a single "result"
error (nothing else can be checked). list_pronunciation_results() takes no
input, so it has no validator.
"""

import math
from datetime import datetime
from typing import Optional

from api.models.foundations.pronunciation_result.exceptions import InvalidPronunciationResultException
from api.models.foundations.pronunciation_result.pronunciation_result import PronunciationResult


class PronunciationResultServiceValidations:
    """Mixin: raises the leaf exception (with every failing field attached)
    when input does not pass checks."""

    def _validate_pronunciation_result_on_create(self, result: Optional[PronunciationResult]) -> None:
        if result is None:
            exception = InvalidPronunciationResultException()
            exception.upsert_data_list("result", "Pronunciation result is required")
            raise exception

        self._validate(
            (not isinstance(result.created_at, datetime), "created_at", "Created at is required"),
            (self._is_blank(result.reference_text), "reference_text", "Reference text is required"),
            (self._is_invalid_score(result.accuracy_score), "accuracy_score", "Accuracy score must be 0 to 100"),
            (self._is_invalid_score(result.fluency_score), "fluency_score", "Fluency score must be 0 to 100"),
            (
                self._is_invalid_score(result.completeness_score),
                "completeness_score",
                "Completeness score must be 0 to 100",
            ),
            (
                self._is_invalid_score(result.pronunciation_score),
                "pronunciation_score",
                "Pronunciation score must be 0 to 100",
            ),
            (
                result.prosody_score is not None and self._is_invalid_score(result.prosody_score),
                "prosody_score",
                "Prosody score must be 0 to 100 when provided",
            ),
            (not isinstance(result.words_json, list), "words_json", "Words must be a list"),
            (self._is_blank(result.locale), "locale", "Locale is required"),
        )

    @staticmethod
    def _is_blank(value: object) -> bool:
        return not isinstance(value, str) or not value.strip()

    @staticmethod
    def _is_invalid_score(value: object) -> bool:
        # bool is an int subclass, so True would otherwise pass as 1.
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return True
        return not math.isfinite(value) or value < 0 or value > 100

    @staticmethod
    def _validate(*rules: tuple[bool, str, str]) -> None:
        exception = InvalidPronunciationResultException()
        for condition, field, message in rules:
            if condition:
                exception.upsert_data_list(field, message)
        exception.throw_if_contains_errors()
