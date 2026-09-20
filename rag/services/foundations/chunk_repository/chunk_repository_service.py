"""Foundation service wrapping ChunkRepositoryBroker.

Single broker dependency -> Foundation layer per CLAUDE.md's Phase 2
Layer-Agent Mapping & Waivers.

Split into this file plus Validations/Exceptions mixins
(chunk_repository_service_validations.py, chunk_repository_service_exceptions.py)
-- mirrors C#'s `partial class` merging EntitlementService.cs /
.Validations.cs / .Exceptions.cs into one class. The concrete class is
declared directly in THIS file, inheriting the other two mixins by name --
no separate "_Base" intermediate class, no composition step in __init__.py.
Matches LearnerProfileService's rebuilt shape exactly. (The previous
`_ChunkRepositoryServiceBase` + __init__.py composition step was the
invented-`_ServiceBase` pattern CLAUDE.md explicitly disallows -- removed.)

Public methods are the ONLY thing that wraps with `_try_catch` (defined in
the Exceptions mixin): each public method's entire body -- validate, then
call the broker -- is an inline nested closure passed straight to
`_try_catch`, not a separate `_do_thing` private method with its own local
try/except. No local try/except inside the closures: every exception --
domain leaf, raw broker exception, or otherwise -- propagates untouched to
`_try_catch`, the single dispatch point that classifies and wraps.
"""

from rag.brokers.chunk_repository import ChunkRepositoryBroker
from rag.brokers.logging import LoggingBroker
from rag.models.foundations.chunk_repository.exceptions import ChunkRepositoryUnavailableError
from rag.models.orchestrations.retrieval import ScoredChunk
from rag.services.foundations.chunk_repository.chunk_repository_service_exceptions import (
    ChunkRepositoryServiceExceptions,
)
from rag.services.foundations.chunk_repository.chunk_repository_service_validations import (
    ChunkRepositoryServiceValidations,
)
from rag.services.foundations.chunk_repository.i_chunk_repository_service import IChunkRepositoryService


class ChunkRepositoryService(
    ChunkRepositoryServiceExceptions,
    ChunkRepositoryServiceValidations,
    IChunkRepositoryService,
):
    """Validates input, then delegates straight to ChunkRepositoryBroker."""

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
        def action() -> int:
            self._validate_insert_chunk_input(topic, source_url, content)
            try:
                return self._chunk_repository.insert_chunk(
                    topic, source_url, content, embedding, embedding_model_version, chunking_strategy_version
                )
            except Exception as e:
                raise ChunkRepositoryUnavailableError(str(e)) from e

        return self._try_catch(action)

    def count_chunks_by_source_url(self, source_url: str) -> int:
        def action() -> int:
            self._validate_blank_field(source_url, "source_url")
            try:
                return self._chunk_repository.count_chunks_by_source_url(source_url)
            except Exception as e:
                raise ChunkRepositoryUnavailableError(str(e)) from e

        return self._try_catch(action)

    def search_by_vector(self, embedding: list[float], top_k: int) -> list[ScoredChunk]:
        def action() -> list[ScoredChunk]:
            self._validate_search_input(top_k)
            try:
                return self._chunk_repository.search_by_vector(embedding, top_k)
            except Exception as e:
                raise ChunkRepositoryUnavailableError(str(e)) from e

        return self._try_catch(action)

    def search_by_text(self, query: str, top_k: int) -> list[ScoredChunk]:
        def action() -> list[ScoredChunk]:
            self._validate_blank_field(query, "query")
            self._validate_search_input(top_k)
            try:
                return self._chunk_repository.search_by_text(query, top_k)
            except Exception as e:
                raise ChunkRepositoryUnavailableError(str(e)) from e

        return self._try_catch(action)
