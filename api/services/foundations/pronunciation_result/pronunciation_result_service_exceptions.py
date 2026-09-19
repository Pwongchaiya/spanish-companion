"""Catch/wrap/log helpers for PronunciationResultService.

Same dispatch shape as SessionLogEntryServiceExceptions: three tiers only
(Validation, Dependency, catch-all Service). No NotFound (nothing is looked
up by id) and no DependencyValidation (no unique constraint), so every
SQLAlchemyError lands on the dependency catch-all.
"""

from typing import Callable, TypeVar

from sqlalchemy.exc import SQLAlchemyError

from api.models.foundations.pronunciation_result.exceptions import (
    FailedPronunciationResultStorageException,
    InvalidPronunciationResultException,
    PronunciationResultDependencyException,
    PronunciationResultServiceException,
    PronunciationResultValidationException,
)

T = TypeVar("T")


class PronunciationResultServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        try:
            return fn()
        except InvalidPronunciationResultException as e:
            raise self._create_and_log_validation_exception(e) from e
        except SQLAlchemyError as e:
            raise self._create_and_log_dependency_exception(FailedPronunciationResultStorageException(str(e))) from e
        except Exception as e:
            raise self._create_and_log_service_exception(e) from e

    def _create_and_log_validation_exception(self, exception: Exception) -> PronunciationResultValidationException:
        validation_exception = PronunciationResultValidationException(inner_exception=exception)
        self._logging_broker.log_error(validation_exception)
        return validation_exception

    def _create_and_log_dependency_exception(self, exception: Exception) -> PronunciationResultDependencyException:
        dependency_exception = PronunciationResultDependencyException(inner_exception=exception)
        self._logging_broker.log_error(dependency_exception)
        return dependency_exception

    def _create_and_log_service_exception(self, exception: Exception) -> PronunciationResultServiceException:
        service_exception = PronunciationResultServiceException(inner_exception=exception)
        self._logging_broker.log_error(service_exception)
        return service_exception
