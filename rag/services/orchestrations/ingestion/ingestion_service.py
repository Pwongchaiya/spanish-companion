"""Ingestion service — chunk, embed, and store one topic's fetched page text.

Coordinates two Foundation services (ChunkRepositoryService +
EmbeddingModelService), so it sits at the Orchestration layer — two
dependencies, satisfying ORC-001's Florance dep-count on its own, and no
direct broker dependency, so ORC-002 needs no waiver either. CLAUDE.md's
Orchestration-row waivers for both codes are what covered the pre-rebuild
shape, where Ingestion wrapped the two brokers directly because no Foundation
layer existed beneath it; that layer now exists.

Fetching is *not* this service's job — the caller (the Ingestion CLI,
hand-written per the same mapping) fetches page text and hands it in. That
keeps `requests`/BeautifulSoup out of the service layer and makes ingest_topic
a pure text -> rows operation.

Split into a base logic file plus Validations/Exceptions mixins (this file,
ingestion_service_validations.py, ingestion_service_exceptions.py), combined
into the concrete IngestionService in __init__.py — mirrors C#'s `partial
class` merging EntitlementCodesOrchestrationService.cs /
.Validations.cs / .Exeptions.cs into one class, the same
multi-inheritance-merge already used for Session Lifecycle and Review in this
codebase.
"""

from rag.brokers.configuration import ConfigurationBroker, EnvConfigurationBroker
from rag.brokers.logging import LoggingBroker, StdlibLoggingBroker
from rag.services.foundations.chunk_repository import IChunkRepositoryService
from rag.services.foundations.embedding_model import IEmbeddingModelService

# Version tags stamped on every row this service writes. Bump CHUNKING_STRATEGY_VERSION
# whenever chunk_text's algorithm changes (size, overlap, splitting rule) and
# read EMBEDDING_MODEL_VERSION from the embedding model service, so the tag records the model
# that actually produced the vectors. Otherwise rows written by different algorithms
# become indistinguishable in the `chunks` table and a targeted re-ingest of just the
# stale ones is impossible. Per the architecture record's "track a chunking-strategy
# version alongside the embedding-model version".
#
# No reference-project analog: this and chunk_text() below are pure MVP business
# logic, carried through this rebuild byte-identical.
CHUNKING_STRATEGY_VERSION = "v1"


def chunk_text(text: str, chunk_size: int) -> list[str]:
    """Split text into fixed-size character chunks, no overlap.

    Phase 1's algorithm (rag/ingest.py chunk_text) unchanged: slice every
    chunk_size characters, strip, drop anything that strips to empty.
    """
    chunks: list[str] = []
    for start in range(0, len(text), chunk_size):
        chunk = text[start : start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
    return chunks


class _IngestionServiceBase:
    """Chunks, embeds, and persists corpus text for one topic.

    The public method delegates to a private `_ingest_topic` through
    `_try_catch` (defined in the Exceptions mixin), mirroring
    EntitlementCodesOrchestrationService.cs:36-65's
    `RedeemEntitlementCodeForUserAsync(...) => TryCatch(async () => {...})`.
    Validation checks are named methods (defined in the Validations mixin)
    rather than inlined, mirroring its sibling .Validations.cs:12-17.
    """

    def __init__(
        self,
        chunk_repository_service: IChunkRepositoryService,
        embedding_model_service: IEmbeddingModelService,
        logging_broker: LoggingBroker = StdlibLoggingBroker(),
        configuration_broker: ConfigurationBroker = EnvConfigurationBroker(),
    ) -> None:
        self._chunk_repository_service = chunk_repository_service
        self._embedding_model_service = embedding_model_service
        # Mirrors the `ILoggingBroker loggingBroker` constructor parameter on
        # EntitlementCodesOrchestrationService.cs:22-33 — every
        # _create_and_log_* method logs through it before raising. Defaulted
        # (unlike the reference's required DI parameter) so the hand-written
        # CLI at rag/controllers/ingestion.py:82 keeps working unchanged;
        # CLAUDE.md's waiver table forbids reshaping that file.
        self._logging_broker = logging_broker
        # Read inside __init__, not at import time (H1) -- same env var and
        # same default as Phase 1's chunker, so re-ingesting produces
        # identical chunks.
        self._chunk_size = int(configuration_broker.get("CHUNK_SIZE", "800"))

    def ingest_topic(self, topic: str, source_url: str, text: str) -> int:
        return self._try_catch(lambda: self._ingest_topic(topic, source_url, text))

    def _ingest_topic(self, topic: str, source_url: str, text: str) -> int:
        # Writes to `chunks` are one-way — ChunkRepositoryBroker has no delete path —
        # and a blank string is not NULL, so it sails past the column's NOT NULL
        # constraint and lands in the corpus permanently. Guard here, before anything
        # is embedded or inserted.
        self._validate_ingest_topic_input(topic, source_url)

        # ponytail: dict.fromkeys is stdlib order-preserving dedupe. Scoped to
        # THIS call only — repeated boilerplate (nav text, a repeated legal
        # footer) can make the fixed-size splitter emit byte-identical chunks
        # from one page. It cannot skip chunks already stored by a previous
        # run: ChunkRepositoryService exposes only insert_chunk and
        # search_by_vector, no read/exists path. True idempotent re-ingestion
        # needs a read method that does not exist yet — see notes.
        chunks = list(dict.fromkeys(chunk_text(text, self._chunk_size)))
        if not chunks:
            return 0

        # No local try/except around either dependency call. Infrastructure
        # failures (sentence-transformers model load, SQLAlchemy, pgvector)
        # are already caught, wrapped, and logged by the Foundation service
        # that owns the broker — arriving here as
        # EmbeddingModelDependencyException / ChunkRepositoryDependencyException,
        # which _try_catch catches directly. That is the reference project's
        # cross-service shape (Exeptions.cs:53-76): the outer service catches
        # the *wrapper* types the layer beneath raises, never re-wraps them
        # into a leaf of its own.
        embeddings = self._embedding_model_service.embed(chunks)

        # Checked up front, not via zip(strict=True) inside the loop: writes have no
        # rollback (there is no delete path), so a mismatch must fail before any row
        # is inserted, not after the loop has already written some.
        self._validate_embeddings_match_chunks(embeddings, chunks)

        for chunk, embedding in zip(chunks, embeddings):
            self._chunk_repository_service.insert_chunk(
                topic=topic,
                source_url=source_url,
                content=chunk,
                embedding=embedding,
                embedding_model_version=self._embedding_model_service.model_name,
                chunking_strategy_version=CHUNKING_STRATEGY_VERSION,
            )

        return len(chunks)
