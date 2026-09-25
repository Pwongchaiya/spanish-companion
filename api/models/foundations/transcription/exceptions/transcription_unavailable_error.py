"""Leaf dependency exception raised when a TranscriptionBroker call fails."""

from api.errors import ApiError


class TranscriptionUnavailableError(ApiError):
    """Raised when TranscriptionBroker.transcribe() fails -- network error, bad credentials,
    cancelled recognition, or timeout. `ResultReason.NoMatch` is NOT this -- it returns an empty
    Transcription instead.

    Mirrors PronunciationAssessmentUnavailableError
    (api/models/foundations/pronunciation_assessment/exceptions/pronunciation_assessment_unavailable_error.py).
    Leaf exception -- always wrapped into TranscriptionDependencyException.
    """
