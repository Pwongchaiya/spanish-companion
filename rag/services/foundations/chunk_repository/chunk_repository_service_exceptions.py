"""Catch/wrap/log helpers for ChunkRepositoryService.

Mirrors Ingestion's ingestion_service_exceptions.py's TryCatch: catch each
known leaf exception, wrap + log it, re-raise the wrapper. Anything else
falls through the final `except Exception` safety net, matching the
reference project's "nothing escapes this service unwrapped" guarantee --
one architectural layer down: Foundation instead of Orchestration, wrapping
one broker directly rather than two.

Same three wrapper tiers Ingestion settled on, same two cited omissions:

1. No DependencyValidation tier -- ChunkRepositoryUnavailableError is an
   infrastructure outage, not a rejected input bubbled up from a layer
   beneath (there is no layer beneath a Foundation service; it calls the
   broker directly).
2. No intermediate Failed*ServiceException before the catch-all -- see
   rag/models/chunk_repository/exceptions/chunk_repository_service_exception.py.
"""

from typing import Callable, TypeVar

from rag.models.chunk_repository.exceptions import (
    ChunkRepositoryDependencyException,
    ChunkRepositoryServiceException,
    ChunkRepositoryUnavailableError,
    ChunkRepositoryValidationException,
    InvalidChunkRepositoryInputError,
)

T = TypeVar("T")


class ChunkRepositoryServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        try:
            return fn()
        except InvalidChunkRepositoryInputError as e:
            raise self._create_and_log_validation_exception(e) from e
        except ChunkRepositoryUnavailableError as e:
            raise self._create_and_log_dependency_exception(e) from e
        except Exception as e:
            raise self._create_and_log_service_exception(e) from e

    def _create_and_log_validation_exception(self, exception: Exception) -> ChunkRepositoryValidationException:
        validation_exception = ChunkRepositoryValidationException(inner_exception=exception)
        self._logging_broker.log_error(validation_exception)
        return validation_exception

    def _create_and_log_dependency_exception(self, exception: Exception) -> ChunkRepositoryDependencyException:
        dependency_exception = ChunkRepositoryDependencyException(inner_exception=exception)
        self._logging_broker.log_error(dependency_exception)
        return dependency_exception

    def _create_and_log_service_exception(self, exception: Exception) -> ChunkRepositoryServiceException:
        service_exception = ChunkRepositoryServiceException(inner_exception=exception)
        self._logging_broker.log_error(service_exception)
        return service_exception
