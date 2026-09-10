"""Base logic for ChunkRepositoryService.

Foundation-tier per CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers:
single broker dependency (ChunkRepositoryBroker), no waiver needed --
identical shape to Generation's _GenerationServiceBase, just wrapping a
different broker.

Split into this base logic file plus Validations and Exceptions mixins
(chunk_repository_service_validations.py, chunk_repository_service_exceptions.py),
combined into the concrete ChunkRepositoryService in __init__.py -- mirrors
C#'s `partial class` merging EntitlementService.cs / .Validations.cs /
.Exeptions.cs into one class, the same multi-inheritance-merge pattern
Ingestion's IngestionService uses one layer up. Unlike Generation, this
service DOES need a Validations mixin: unlike explain()'s flag/chunk
objects (already validated upstream by the time Generation sees them),
insert_chunk/search_by_vector are the first stop for raw caller input, and
a blank topic/source_url/content would otherwise sail into the `chunks`
table (which has no delete path, per Ingestion's own docstring) or top_k=0
would silently ask the broker for zero rows.
"""

from rag.brokers.chunk_repository import ChunkRepositoryBroker
from rag.brokers.logging import LoggingBroker
from rag.models.chunk_repository.exceptions import ChunkRepositoryUnavailableError
from rag.models.retrieval import ScoredChunk


class _ChunkRepositoryServiceBase:
    """Validates input, then delegates straight to ChunkRepositoryBroker.

    Each public method delegates through `_try_catch` (defined in the
    Exceptions mixin) to a private method of the same name, mirroring
    IngestionService's `ingest_topic` -> `_ingest_topic` split one layer up.
    """

    def __init__(
        self,
        chunk_repository: ChunkRepositoryBroker,
        *,
        logging_broker: LoggingBroker,
    ) -> None:
        self._chunk_repository = chunk_repository
        self._logging_broker = logging_broker

    def insert_chunk(
        self,
        topic: str,
        source_url: str,
        content: str,
        embedding: list[float],
        embedding_model_version: str,
        chunking_strategy_version: str,
    ) -> int:
        return self._try_catch(
            lambda: self._insert_chunk(
                topic, source_url, content, embedding, embedding_model_version, chunking_strategy_version
            )
        )

    def _insert_chunk(
        self,
        topic: str,
        source_url: str,
        content: str,
        embedding: list[float],
        embedding_model_version: str,
        chunking_strategy_version: str,
    ) -> int:
        self._validate_insert_chunk_input(topic, source_url, content)
        try:
            return self._chunk_repository.insert_chunk(
                topic, source_url, content, embedding, embedding_model_version, chunking_strategy_version
            )
        except Exception as e:
            raise ChunkRepositoryUnavailableError(str(e)) from e

    def search_by_vector(self, embedding: list[float], top_k: int) -> list[ScoredChunk]:
        return self._try_catch(lambda: self._search_by_vector(embedding, top_k))

    def _search_by_vector(self, embedding: list[float], top_k: int) -> list[ScoredChunk]:
        self._validate_search_input(top_k)
        try:
            return self._chunk_repository.search_by_vector(embedding, top_k)
        except Exception as e:
            raise ChunkRepositoryUnavailableError(str(e)) from e
