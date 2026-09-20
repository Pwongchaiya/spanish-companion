"""Validation checks for SessionAudioService.

Same batched predicate pattern as PersonaServiceValidations: every failing
field is reported in one InvalidSessionAudioException.
"""

from datetime import datetime
from typing import Optional

from api.models.foundations.session_audio.exceptions import InvalidSessionAudioException
from api.models.foundations.session_audio.session_audio import SessionAudio


class SessionAudioServiceValidations:
    """Mixin: raises the leaf exception (with every failing field attached)
    when input does not pass checks."""

    def _validate_session_audio_on_create(self, session_audio: Optional[SessionAudio]) -> None:
        if session_audio is None:
            exception = InvalidSessionAudioException()
            exception.upsert_data_list("session_audio", "Session audio is required")
            raise exception

        self._validate(
            (self._is_invalid_id(session_audio.session_log_id), "session_log_id", "Session log id is required"),
            (
                not isinstance(session_audio.file_path, str) or not session_audio.file_path.strip(),
                "file_path",
                "File path is required",
            ),
            (
                isinstance(session_audio.duration_seconds, bool)
                or not isinstance(session_audio.duration_seconds, (int, float))
                or session_audio.duration_seconds < 0,
                "duration_seconds",
                "Duration must be a non-negative number",
            ),
            (not isinstance(session_audio.created_at, datetime), "created_at", "Created at is required"),
        )

    def _validate_id(self, field: str, value: object) -> None:
        self._validate((self._is_invalid_id(value), field, f"{field} is required"))

    def _validate_cutoff(self, cutoff: object) -> None:
        self._validate((not isinstance(cutoff, datetime), "cutoff", "Cutoff is required"))

    @staticmethod
    def _is_invalid_id(value: object) -> bool:
        # bool is an int subclass, so True would otherwise pass as 1.
        return isinstance(value, bool) or not isinstance(value, int) or value <= 0

    @staticmethod
    def _validate(*rules: tuple[bool, str, str]) -> None:
        exception = InvalidSessionAudioException()
        for condition, field, message in rules:
            if condition:
                exception.upsert_data_list(field, message)
        exception.throw_if_contains_errors()
