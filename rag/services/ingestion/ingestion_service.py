"""Ingestion service — chunk, embed, and store one topic's fetched page text.

Coordinates two brokers (ChunkRepositoryBroker + EmbeddingModelBroker), so it
sits at the Orchestration layer per CLAUDE.md's Phase 2 Layer-Agent Mapping.
ORC-001 (Florance dep-count) and ORC-002 (no direct broker deps) are waived
there: this project has no Foundation layer beneath Ingestion, so depending on
brokers directly is the intended shape, not a violation.

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

import os

from dotenv import load_dotenv

from rag.brokers.chunk_repository import ChunkRepositoryBroker
from rag.brokers.embedding_model import EmbeddingModelBroker
from rag.brokers.logging import LoggingBroker, StdlibLoggingBroker
from rag.models.ingestion.exceptions import IngestionUnavailableError

load_dotenv()

# ponytail: one knob -> plain os.getenv at import time, same pattern as
# rag/ingest.py and api/services/session_lifecycle/. Same env var and same
# default as Phase 1's chunker, so re-ingesting produces identical chunks.
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))

# Version tags stamped on every row this service writes. Bump CHUNKING_STRATEGY_VERSION
# whenever chunk_text's algorithm changes (size, overlap, splitting rule) and
# read EMBEDDING_MODEL_VERSION from the broker instance, so the tag records the model
# that actually produced the vectors. Otherwise rows written by different algorithms
# become indistinguishable in the `chunks` table and a targeted re-ingest of just the
# stale ones is impossible. Per the architecture record's "track a chunking-strategy
# version alongside the embedding-model version".
#
# No reference-project analog: this and chunk_text() below are pure MVP business
# logic, carried through this rebuild byte-identical.
CHUNKING_STRATEGY_VERSION = "v1"


def chunk_text(text: str) -> list[str]:
    """Split text into fixed-size character chunks, no overlap.

    Phase 1's algorithm (rag/ingest.py chunk_text) unchanged: slice every
    CHUNK_SIZE characters, strip, drop anything that strips to empty.
    """
    chunks: list[str] = []
    for start in range(0, len(text), CHUNK_SIZE):
        chunk = text[start : start + CHUNK_SIZE].strip()
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
        chunk_repository: ChunkRepositoryBroker,
        embedding_model: EmbeddingModelBroker,
        logging_broker: LoggingBroker = StdlibLoggingBroker(),
    ) -> None:
        self._chunk_repository = chunk_repository
        self._embedding_model = embedding_model
        # Mirrors the `ILoggingBroker loggingBroker` constructor parameter on
        # EntitlementCodesOrchestrationService.cs:22-33 — every
        # _create_and_log_* method logs through it before raising. Defaulted
        # (unlike the reference's required DI parameter) so the hand-written
        # CLI at rag/controllers/ingestion.py:82 keeps working unchanged;
        # CLAUDE.md's waiver table forbids reshaping that file.
        self._logging_broker = logging_broker

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
        # run: ChunkRepositoryBroker exposes only insert_chunk and
        # search_by_vector, no read/exists path. True idempotent re-ingestion
        # needs a broker read method that does not exist yet — see notes.
        chunks = list(dict.fromkeys(chunk_text(text)))
        if not chunks:
            return 0

        # Broker failures (sentence-transformers model load, SQLAlchemy,
        # pgvector) are wrapped into one named leaf here, then into
        # IngestionOrchestrationDependencyException by _try_catch. Same two
        # wrap sites, same `raise X(str(e)) from e` shape, as
        # RetrievalUnavailableError in
        # rag/services/retrieval/retrieval_service.py:121-124 and :132-135.
        try:
            embeddings = self._embedding_model.embed(chunks)
        except Exception as e:
            raise IngestionUnavailableError(str(e)) from e

        # Checked up front, not via zip(strict=True) inside the loop: writes have no
        # rollback (ChunkRepositoryBroker has no delete path), so a mismatch must fail
        # before any row is inserted, not after the loop has already written some.
        self._validate_embeddings_match_chunks(embeddings, chunks)

        try:
            for chunk, embedding in zip(chunks, embeddings):
                self._chunk_repository.insert_chunk(
                    topic=topic,
                    source_url=source_url,
                    content=chunk,
                    embedding=embedding,
                    embedding_model_version=self._embedding_model.model_name,
                    chunking_strategy_version=CHUNKING_STRATEGY_VERSION,
                )
        except Exception as e:
            raise IngestionUnavailableError(str(e)) from e

        return len(chunks)
