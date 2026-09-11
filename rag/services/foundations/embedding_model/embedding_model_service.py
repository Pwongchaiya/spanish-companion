"""EmbeddingModelService -- Foundation service wrapping EmbeddingModelBroker.

One broker dependency, so this sits at the Foundation layer per CLAUDE.md's
Phase 2 Layer-Agent Mapping -- one layer below Ingestion/Retrieval's
Orchestration tier, which wraps two brokers each. No Processing layer exists
beneath it (nothing in this codebase needs higher-order logic on top of raw
embedding), so this Foundation service wraps the broker directly, matching
how every other single-broker Service in this rebuild is built.

Split into a base logic file plus Validations/Exceptions mixins (this file,
embedding_model_service_validations.py, embedding_model_service_exceptions.py)
-- mirrors C#'s `partial class` merging pattern. The concrete class is
declared directly in THIS file, inheriting the other two mixins by name --
no separate "_Base" intermediate class, no composition step in __init__.py.
Matches LearnerProfileService's rebuilt shape
(api/services/foundations/learner_profile/learner_profile_service.py).

Public methods are the ONLY thing that wraps with `_try_catch` (defined in
the Exceptions mixin): `embed`'s entire body -- validate, then call the
broker -- is an inline nested closure passed straight to `_try_catch`, not a
separate `_embed` private method. `model_name` stays an unwrapped passthrough
-- no failure mode on the broker's `model_name` property to wrap, same
reasoning as ReviewOrchestrationService.list_flags().
"""

from typing import List

from rag.brokers.embedding_model import EmbeddingModelBroker
from rag.brokers.logging import LoggingBroker
from rag.models.foundations.embedding_model.exceptions import EmbeddingModelUnavailableError
from rag.services.foundations.embedding_model.embedding_model_service_exceptions import (
    EmbeddingModelServiceExceptions,
)
from rag.services.foundations.embedding_model.embedding_model_service_validations import (
    EmbeddingModelServiceValidations,
)
from rag.services.foundations.embedding_model.i_embedding_model_service import IEmbeddingModelService


class EmbeddingModelService(
    EmbeddingModelServiceExceptions,
    EmbeddingModelServiceValidations,
    IEmbeddingModelService,
):
    """Validates input, then delegates to EmbeddingModelBroker."""

    def __init__(
        self,
        embedding_model: EmbeddingModelBroker,
        *,
        logging_broker: LoggingBroker,
    ) -> None:
        self._embedding_model = embedding_model
        # Mirrors the `ILoggingBroker loggingBroker` constructor parameter
        # every Service in this rebuild takes -- every _create_and_log_*
        # method logs through it before raising. Defaulted, same as
        # Ingestion's constructor, since nothing wires a real broker in yet.
        self._logging_broker = logging_broker

    @property
    def model_name(self) -> str:
        # ponytail: pure passthrough, no failure mode on the broker's
        # `model_name` property to wrap -- not routed through _try_catch,
        # same reasoning as ReviewOrchestrationService.list_flags()
        # (api/services/review/review_service.py:90-99)'s deliberately
        # unwrapped passthrough.
        return self._embedding_model.model_name

    def embed(self, texts: List[str]) -> List[List[float]]:
        def action() -> List[List[float]]:
            self._validate_embed_input(texts)

            # The one broker call site. Wrapped into a named leaf here, then
            # into EmbeddingModelDependencyException by _try_catch -- same
            # `raise X(str(e)) from e` shape as IngestionUnavailableError's
            # `embed` call site in rag/services/ingestion/ingestion_service.py.
            try:
                return self._embedding_model.embed(texts)
            except Exception as e:
                raise EmbeddingModelUnavailableError(str(e)) from e

        return self._try_catch(action)
