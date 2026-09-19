"""Catch/wrap/log helpers for PronunciationAssessmentService.

Mirrors TtsServiceExceptions (api/services/foundations/tts/tts_service_exceptions.py).
"""

from typing import Callable, TypeVar

from api.models.foundations.pronunciation_assessment.exceptions import (
    InvalidPronunciationAssessmentRequestException,
    PronunciationAssessmentDependencyException,
    PronunciationAssessmentServiceException,
    PronunciationAssessmentUnavailableError,
    PronunciationAssessmentValidationException,
)

T = TypeVar("T")


class PronunciationAssessmentServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        try:
            return fn()
        except InvalidPronunciationAssessmentRequestException as e:
            raise self._create_and_log_validation_exception(e) from e
        except PronunciationAssessmentUnavailableError as e:
            raise self._create_and_log_dependency_exception(e) from e
        except Exception as e:
            raise self._create_and_log_service_exception(e) from e

    def _create_and_log_validation_exception(self, exception: Exception) -> PronunciationAssessmentValidationException:
        wrapped = PronunciationAssessmentValidationException(inner_exception=exception)
        self._logging_broker.log_error(wrapped)
        return wrapped

    def _create_and_log_dependency_exception(self, exception: Exception) -> PronunciationAssessmentDependencyException:
        wrapped = PronunciationAssessmentDependencyException(inner_exception=exception)
        self._logging_broker.log_error(wrapped)
        return wrapped

    def _create_and_log_service_exception(self, exception: Exception) -> PronunciationAssessmentServiceException:
        wrapped = PronunciationAssessmentServiceException(inner_exception=exception)
        self._logging_broker.log_error(wrapped)
        return wrapped
