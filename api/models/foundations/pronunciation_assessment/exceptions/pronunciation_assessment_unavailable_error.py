"""Leaf dependency exception raised when a PronunciationAssessmentBroker call fails."""

from api.errors import ApiError


class PronunciationAssessmentUnavailableError(ApiError):
    """Raised when PronunciationAssessmentBroker.assess() fails -- network error, bad credentials,
    no-match/cancelled recognition, or timeout.

    Mirrors TtsUnavailableError (api/models/foundations/tts/exceptions/tts_unavailable_error.py).
    Leaf exception -- always wrapped into PronunciationAssessmentDependencyException.
    """
