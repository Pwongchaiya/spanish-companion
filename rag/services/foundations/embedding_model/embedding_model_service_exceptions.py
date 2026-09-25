"""Catch/wrap/log helpers for EmbeddingModelService.

Mirrors rag/services/ingestion/ingestion_service_exceptions.py's TryCatch
shape one layer down, at the Foundation tier: catch each known leaf
exception, wrap + log it, re-raise the wrapper; anything else falls through
the final `except Exception` safety net, matching the reference project's
"nothing escapes this service unwrapped" guarantee.

Same three-wrapper-tier collapse Ingestion already made, unchanged here:

1. No DependencyValidation tier -- EmbeddingModelUnavailableError is an
   infrastructure outage, not a rejected input bubbled up from a layer
   beneath (there is no layer beneath a Foundation service; it wraps its one
   broker directly).
2. No intermediate Failed*ServiceException before the catch-all -- see
   rag/models/foundations/embedding_model/exceptions/embedding_model_service_exception.py
   for the full reasoning, cited from Ingestion's equivalent file.
"""

from typing import Callable, TypeVar

from rag.models.foundations.embedding_model.exceptions import (
    EmbeddingModelDependencyException,
    EmbeddingModelServiceException,
    EmbeddingModelUnavailableError,
    EmbeddingModelValidationException,
    InvalidEmbeddingModelInputError,
)

T = TypeVar("T")


class EmbeddingModelServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        try:
            return fn()
        except InvalidEmbeddingModelInputError as e:
            raise self._create_and_log_validation_exception(e) from e
        except EmbeddingModelUnavailableError as e:
            raise self._create_and_log_dependency_exception(e) from e
        except Exception as e:
            raise self._create_and_log_service_exception(e) from e

    def _create_and_log_validation_exception(self, exception: Exception) -> EmbeddingModelValidationException:
        validation_exception = EmbeddingModelValidationException(inner_exception=exception)
        self._logging_broker.log_error(validation_exception)
        return validation_exception

    def _create_and_log_dependency_exception(self, exception: Exception) -> EmbeddingModelDependencyException:
        dependency_exception = EmbeddingModelDependencyException(inner_exception=exception)
        self._logging_broker.log_error(dependency_exception)
        return dependency_exception

    def _create_and_log_service_exception(self, exception: Exception) -> EmbeddingModelServiceException:
        service_exception = EmbeddingModelServiceException(inner_exception=exception)
        self._logging_broker.log_error(service_exception)
        return service_exception
