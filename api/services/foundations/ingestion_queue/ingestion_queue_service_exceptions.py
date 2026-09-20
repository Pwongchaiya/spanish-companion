"""Catch/wrap/log helpers for IngestionQueueService.

Same specific-exception-type dispatch table as TopicCoveredServiceExceptions:
validation leaves -> validation wrapper, unique-violation IntegrityError ->
dependency-validation wrapper, other SQLAlchemyError -> dependency wrapper,
everything else -> service wrapper.
"""

from typing import Callable, TypeVar

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from api.models.foundations.ingestion_queue.exceptions import (
    AlreadyExistsIngestionQueueException,
    FailedIngestionQueueStorageException,
    IngestionQueueDependencyException,
    IngestionQueueDependencyValidationException,
    IngestionQueueServiceException,
    IngestionQueueValidationException,
    InvalidIngestionQueueException,
    NotFoundIngestionQueueException,
)

T = TypeVar("T")

# Postgres/pg8000's unique-violation message contains one of these phrases
# (sqlite's says "UNIQUE constraint failed"); NOT NULL/CHECK violations do not.
_UNIQUE_VIOLATION_MARKERS = ("unique constraint", "duplicate key")


class IngestionQueueServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        try:
            return fn()
        except InvalidIngestionQueueException as e:
            raise self._create_and_log_validation_exception(e) from e
        except NotFoundIngestionQueueException as e:
            raise self._create_and_log_validation_exception(e) from e
        except IntegrityError as e:
            if self._is_unique_violation(e):
                already_exists = AlreadyExistsIngestionQueueException("Ingestion queue row already exists for topic.")
                raise self._create_and_log_dependency_validation_exception(already_exists) from e
            raise self._create_and_log_dependency_exception(FailedIngestionQueueStorageException(str(e))) from e
        except SQLAlchemyError as e:
            raise self._create_and_log_dependency_exception(FailedIngestionQueueStorageException(str(e))) from e
        except Exception as e:
            raise self._create_and_log_service_exception(e) from e

    @staticmethod
    def _is_unique_violation(error: IntegrityError) -> bool:
        message = str(error.orig if error.orig is not None else error).lower()
        return any(marker in message for marker in _UNIQUE_VIOLATION_MARKERS)

    def _create_and_log_validation_exception(self, exception: Exception) -> IngestionQueueValidationException:
        validation_exception = IngestionQueueValidationException(inner_exception=exception)
        self._logging_broker.log_error(validation_exception)
        return validation_exception

    def _create_and_log_dependency_exception(self, exception: Exception) -> IngestionQueueDependencyException:
        dependency_exception = IngestionQueueDependencyException(inner_exception=exception)
        self._logging_broker.log_error(dependency_exception)
        return dependency_exception

    def _create_and_log_dependency_validation_exception(
        self, exception: Exception
    ) -> IngestionQueueDependencyValidationException:
        dependency_validation_exception = IngestionQueueDependencyValidationException(inner_exception=exception)
        self._logging_broker.log_error(dependency_validation_exception)
        return dependency_validation_exception

    def _create_and_log_service_exception(self, exception: Exception) -> IngestionQueueServiceException:
        service_exception = IngestionQueueServiceException(inner_exception=exception)
        self._logging_broker.log_error(service_exception)
        return service_exception
