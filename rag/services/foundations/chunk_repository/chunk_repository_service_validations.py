"""Validation checks for ChunkRepositoryService.

Mirrors Ingestion's ingestion_service_validations.py -- named
`_validate_<thing>_input` aggregator calling one named per-field check each
-- one layer down: Foundation instead of Orchestration, and the checks here
guard this service's own two public methods directly rather than a single
`ingest_topic` entry point.

Same collapse already recorded in Ingestion's validations file: no
rule/accumulator machinery, just `if condition: raise LeafException(message)`,
failing on the first bad field rather than accumulating all of them.
"""

from rag.models.foundations.chunk_repository.exceptions import InvalidChunkRepositoryInputError


class ChunkRepositoryServiceValidations:
    """Mixin: raises the leaf validation exception when input is unusable.

    See chunk_repository_service_exceptions.py for how these get wrapped and
    logged before leaving the service.
    """

    def _validate_insert_chunk_input(self, topic: str, source_url: str, content: str) -> None:
        self._validate_blank_field(topic, "topic")
        self._validate_blank_field(source_url, "source_url")
        self._validate_blank_field(content, "content")

    def _validate_blank_field(self, value: str, field_name: str) -> None:
        if not value or not value.strip():
            raise InvalidChunkRepositoryInputError(f"{field_name} is required")

    def _validate_search_input(self, top_k: int) -> None:
        if top_k < 1:
            raise InvalidChunkRepositoryInputError("top_k must be at least 1")
