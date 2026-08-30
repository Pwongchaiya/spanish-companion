"""Interface for the EmbeddingModel Foundation service.

Mirrors rag/services/ingestion/i_ingestion_service.py's shape one layer down:
typing.Protocol, not abc.ABC, per this project's broker-interface waiver
(CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers table), co-located with
its implementation the same way every Protocol interface in this rebuild is.

Unlike Ingestion, the concrete class name `EmbeddingModelService` was free
for the Protocol to take too -- no prior class claimed it -- but the `I`
prefix is kept anyway for the same reason the Foundation Agent's own
briefing names: this rebuild's convention keeps the reference's literal `I`
prefix on every service Protocol regardless of whether the plain name was
free, matching `IIngestionService` / `IEmbeddingModelBroker`-style naming
used one layer either side of this one.
"""

from typing import List, Protocol


class IEmbeddingModelService(Protocol):
    """External-facing contract for the EmbeddingModel Foundation service."""

    @property
    def model_name(self) -> str:
        """The model name the underlying broker is configured to use.

        Pure passthrough to EmbeddingModelBroker.model_name -- no failure
        mode, so it is not wrapped in any exception.
        """
        ...

    def embed(self, texts: List[str]) -> List[List[float]]:
        """One 384-dim vector per text, same order.

        Raises:
            EmbeddingModelValidationException: wrapping
                InvalidEmbeddingModelInputError -- `texts` is empty, or any
                element is blank/whitespace-only.
            EmbeddingModelDependencyException: wrapping
                EmbeddingModelUnavailableError -- the embedding model broker
                is unreachable or fails.
            EmbeddingModelServiceException: anything else.
        """
        ...


__all__ = ["IEmbeddingModelService"]
