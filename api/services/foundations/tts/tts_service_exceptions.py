"""Catch/wrap/log helpers for TtsService.

Mirrors FlagServiceExceptions' 3-bucket dispatch shape
(api/services/foundations/flag/flag_service_exceptions.py) --
`_try_catch` returns fn()'s value since synthesize_speech() produces bytes.
"""

from typing import Callable, TypeVar

from api.models.foundations.tts.exceptions import (
    InvalidTtsRequestException,
    TtsDependencyException,
    TtsServiceException,
    TtsUnavailableError,
    TtsValidationException,
)

T = TypeVar("T")


class TtsServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        try:
            return fn()
        except InvalidTtsRequestException as e:
            raise self._create_and_log_validation_exception(e) from e
        except TtsUnavailableError as e:
            raise self._create_and_log_dependency_exception(e) from e
        except Exception as e:
            raise self._create_and_log_service_exception(e) from e

    def _create_and_log_validation_exception(self, exception: Exception) -> TtsValidationException:
        validation_exception = TtsValidationException(inner_exception=exception)
        self._logging_broker.log_error(validation_exception)
        return validation_exception

    def _create_and_log_dependency_exception(self, exception: Exception) -> TtsDependencyException:
        dependency_exception = TtsDependencyException(inner_exception=exception)
        self._logging_broker.log_error(dependency_exception)
        return dependency_exception

    def _create_and_log_service_exception(self, exception: Exception) -> TtsServiceException:
        service_exception = TtsServiceException(inner_exception=exception)
        self._logging_broker.log_error(service_exception)
        return service_exception
