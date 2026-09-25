"""Catch/wrap/log helpers for TranscriptionService.

Mirrors PronunciationAssessmentServiceExceptions
(api/services/foundations/pronunciation_assessment/pronunciation_assessment_service_exceptions.py).
"""

from typing import Callable, TypeVar

from api.models.foundations.transcription.exceptions import (
    InvalidTranscriptionRequestException,
    TranscriptionDependencyException,
    TranscriptionServiceException,
    TranscriptionUnavailableError,
    TranscriptionValidationException,
)

T = TypeVar("T")


class TranscriptionServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        try:
            return fn()
        except InvalidTranscriptionRequestException as e:
            raise self._create_and_log_validation_exception(e) from e
        except TranscriptionUnavailableError as e:
            raise self._create_and_log_dependency_exception(e) from e
        except Exception as e:
            raise self._create_and_log_service_exception(e) from e

    def _create_and_log_validation_exception(self, exception: Exception) -> TranscriptionValidationException:
        wrapped = TranscriptionValidationException(inner_exception=exception)
        self._logging_broker.log_error(wrapped)
        return wrapped

    def _create_and_log_dependency_exception(self, exception: Exception) -> TranscriptionDependencyException:
        wrapped = TranscriptionDependencyException(inner_exception=exception)
        self._logging_broker.log_error(wrapped)
        return wrapped

    def _create_and_log_service_exception(self, exception: Exception) -> TranscriptionServiceException:
        wrapped = TranscriptionServiceException(inner_exception=exception)
        self._logging_broker.log_error(wrapped)
        return wrapped
