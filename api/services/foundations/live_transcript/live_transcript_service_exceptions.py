"""Catch/wrap/log helpers for LiveTranscriptService.

Mirrors flag_service_exceptions.py's TryCatch shape. Two wrapper tiers, not
three: nothing here is validation-shaped (see the base class's docstring),
so there is no validation branch to add.
"""

from typing import Callable, TypeVar

from api.models.foundations.live_transcript.exceptions import (
    LiveTranscriptDependencyException,
    LiveTranscriptServiceException,
    LiveTranscriptUnavailableError,
)

T = TypeVar("T")


class LiveTranscriptServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        try:
            return fn()
        except LiveTranscriptUnavailableError as e:
            raise self._create_and_log_dependency_exception(e) from e
        except Exception as e:
            raise self._create_and_log_service_exception(e) from e

    def _create_and_log_dependency_exception(self, exception: Exception) -> LiveTranscriptDependencyException:
        dependency_exception = LiveTranscriptDependencyException(inner_exception=exception)
        self._logging_broker.log_error(dependency_exception)
        return dependency_exception

    def _create_and_log_service_exception(self, exception: Exception) -> LiveTranscriptServiceException:
        service_exception = LiveTranscriptServiceException(inner_exception=exception)
        self._logging_broker.log_error(service_exception)
        return service_exception
