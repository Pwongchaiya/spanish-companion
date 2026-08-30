"""EmbeddingModelService -- Foundation service wrapping EmbeddingModelBroker.

One broker dependency, so this sits at the Foundation layer per CLAUDE.md's
Phase 2 Layer-Agent Mapping -- one layer below Ingestion/Retrieval's
Orchestration tier, which wraps two brokers each. No Processing layer exists
beneath it (nothing in this codebase needs higher-order logic on top of raw
embedding), so this Foundation service wraps the broker directly, matching
how every other single-broker Service in this rebuild is built.

Split into a base logic file plus Validations/Exceptions mixins (this file,
embedding_model_service_validations.py, embedding_model_service_exceptions.py),
combined into the concrete EmbeddingModelService in __init__.py -- the same
3-mixin split rag/services/ingestion uses one layer up, itself mirroring C#'s
`partial class` merging EntitlementCodesOrchestrationService.cs / .Validations.cs
/ .Exeptions.cs into one class.
"""

from typing import List

from rag.brokers.embedding_model import EmbeddingModelBroker
from rag.brokers.logging import LoggingBroker, StdlibLoggingBroker
from rag.models.embedding_model.exceptions import EmbeddingModelUnavailableError


class _EmbeddingModelServiceBase:
    """Validates input, then delegates to EmbeddingModelBroker.

    The public `embed` method delegates to a private `_embed` through
    `_try_catch` (defined in the Exceptions mixin), mirroring
    `_IngestionServiceBase.ingest_topic`'s same delegation one layer up.
    """

    def __init__(
        self,
        embedding_model: EmbeddingModelBroker,
        logging_broker: LoggingBroker = StdlibLoggingBroker(),
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
        # same reasoning as ReviewOrchestrator.list_flags()
        # (api/services/review/review_service.py:90-99)'s deliberately
        # unwrapped passthrough.
        return self._embedding_model.model_name

    def embed(self, texts: List[str]) -> List[List[float]]:
        return self._try_catch(lambda: self._embed(texts))

    def _embed(self, texts: List[str]) -> List[List[float]]:
        self._validate_embed_input(texts)

        # The one broker call site. Wrapped into a named leaf here, then
        # into EmbeddingModelDependencyException by _try_catch -- same
        # `raise X(str(e)) from e` shape as IngestionUnavailableError's
        # `embed` call site in rag/services/ingestion/ingestion_service.py.
        try:
            return self._embedding_model.embed(texts)
        except Exception as e:
            raise EmbeddingModelUnavailableError(str(e)) from e
