"""Interface for the Chunk Repository Foundation-tier service.

Mirrors NL.Core.Entitlements.Api/Services/Foundations/Entitlements/
IEntitlementService.cs:12-19 -- typing.Protocol, not abc.ABC, per this
project's broker-interface waiver (CLAUDE.md's Phase 2 Layer-Agent Mapping
& Waivers table), extended to service interfaces the same way
rag/services/generation/i_generation_service.py and Session Lifecycle's
i_session_lifecycle_service.py already do: the reference project itself
co-locates the interface file with its implementation, same folder.

Keeps the reference's literal `I` prefix on the class name --
`IChunkRepositoryService` -- exactly as rag/services/ingestion/
i_ingestion_service.py's IIngestionService does, and for the identical
reason: the concrete class must stay `ChunkRepositoryService` (this
rebuild's naming convention pins it), so the feature name is not free to
give to the Protocol here.
"""

from typing import Protocol

from rag.models.orchestrations.retrieval import ScoredChunk


class IChunkRepositoryService(Protocol):
    """External-facing contract for the Chunk Repository Foundation service."""

    def insert_chunk(
        self,
        topic: str,
        source_url: str,
        content: str,
        embedding: list[float],
        embedding_model_version: str,
        chunking_strategy_version: str,
    ) -> int:
        """Validate input, then delegate to ChunkRepositoryBroker.insert_chunk.

        Raises:
            ChunkRepositoryValidationException: wrapping
                InvalidChunkRepositoryInputError -- blank `topic`, blank
                `source_url`, or blank `content`.
            ChunkRepositoryDependencyException: wrapping
                ChunkRepositoryUnavailableError -- the broker call failed.
            ChunkRepositoryServiceException: anything else unexpected.
        """
        ...

    def count_chunks_by_source_url(self, source_url: str) -> int:
        """Validate input, then delegate to ChunkRepositoryBroker.count_chunks_by_source_url.

        Raises:
            ChunkRepositoryValidationException: wrapping
                InvalidChunkRepositoryInputError -- blank `source_url`.
            ChunkRepositoryDependencyException: wrapping
                ChunkRepositoryUnavailableError -- the broker call failed.
            ChunkRepositoryServiceException: anything else unexpected.
        """
        ...

    def delete_chunks_by_source_url(self, source_url: str) -> int:
        """Validate input, then delegate to ChunkRepositoryBroker.delete_chunks_by_source_url.

        Raises:
            ChunkRepositoryValidationException: wrapping
                InvalidChunkRepositoryInputError -- blank `source_url`.
            ChunkRepositoryDependencyException: wrapping
                ChunkRepositoryUnavailableError -- the broker call failed.
            ChunkRepositoryServiceException: anything else unexpected.
        """
        ...

    def search_by_vector(self, embedding: list[float], top_k: int) -> list[ScoredChunk]:
        """Validate input, then delegate to ChunkRepositoryBroker.search_by_vector.

        Raises:
            ChunkRepositoryValidationException: wrapping
                InvalidChunkRepositoryInputError -- `top_k < 1`.
            ChunkRepositoryDependencyException: wrapping
                ChunkRepositoryUnavailableError -- the broker call failed.
            ChunkRepositoryServiceException: anything else unexpected.
        """
        ...


    def search_by_text(self, query: str, top_k: int) -> list[ScoredChunk]:
        """Validate input, then delegate to ChunkRepositoryBroker.search_by_text.

        Raises:
            ChunkRepositoryValidationException: wrapping
                InvalidChunkRepositoryInputError -- blank `query` or `top_k < 1`.
            ChunkRepositoryDependencyException: wrapping
                ChunkRepositoryUnavailableError -- the broker call failed.
            ChunkRepositoryServiceException: anything else unexpected.
        """
        ...


__all__ = ["IChunkRepositoryService"]
