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

Broker exceptions (SQLAlchemy, pgvector, model load) propagate unwrapped: the
architecture record names no ingestion-specific exception, and inventing a
hierarchy for zero named cases is the exception-hierarchy waiver's whole point.
"""

import os

from dotenv import load_dotenv

from rag.brokers.chunk_repository import ChunkRepositoryBroker
from rag.brokers.embedding_model import EmbeddingModelBroker
from rag.errors import RagError

load_dotenv()

# ponytail: one knob -> plain os.getenv at import time, same pattern as
# rag/ingest.py and api/services/session_lifecycle.py. Same env var and same
# default as Phase 1's chunker, so re-ingesting produces identical chunks.
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))

# Version tags stamped on every row this service writes. Bump CHUNKING_STRATEGY_VERSION
# whenever chunk_text's algorithm changes (size, overlap, splitting rule) and
# read EMBEDDING_MODEL_VERSION from the broker instance, so the tag records the model
# that actually produced the vectors. Otherwise rows written by different algorithms
# become indistinguishable in the `chunks` table and a targeted re-ingest of just the
# stale ones is impossible. Per the architecture record's "track a chunking-strategy
# version alongside the embedding-model version".
CHUNKING_STRATEGY_VERSION = "v1"


class IngestionValidationError(RagError):
    """Raised when ingestion input fails validation."""


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


class IngestionService:
    """Chunks, embeds, and persists corpus text for one topic."""

    def __init__(self, chunk_repository: ChunkRepositoryBroker, embedding_model: EmbeddingModelBroker) -> None:
        self._chunk_repository = chunk_repository
        self._embedding_model = embedding_model

    def ingest_topic(self, topic: str, source_url: str, text: str) -> int:
        """Chunk `text`, embed the chunks in one batch, insert each. Returns rows inserted.

        Empty or whitespace-only `text` yields zero chunks and returns 0 without
        touching either broker.

        Raises IngestionValidationError if `topic` or `source_url` is missing or blank.
        """
        # Writes to `chunks` are one-way — ChunkRepositoryBroker has no delete path —
        # and a blank string is not NULL, so it sails past the column's NOT NULL
        # constraint and lands in the corpus permanently. Guard here, before anything
        # is embedded or inserted.
        if not topic or not topic.strip():
            raise IngestionValidationError("topic is required")
        if not source_url or not source_url.strip():
            raise IngestionValidationError("source_url is required")

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

        embeddings = self._embedding_model.embed(chunks)

        # Checked up front, not via zip(strict=True) inside the loop: writes have no
        # rollback (ChunkRepositoryBroker has no delete path), so a mismatch must fail
        # before any row is inserted, not after the loop has already written some.
        if len(embeddings) != len(chunks):
            raise IngestionValidationError(f"embedding count {len(embeddings)} does not match chunk count {len(chunks)}")

        for chunk, embedding in zip(chunks, embeddings):
            self._chunk_repository.insert_chunk(
                topic=topic,
                source_url=source_url,
                content=chunk,
                embedding=embedding,
                embedding_model_version=self._embedding_model.model_name,
                chunking_strategy_version=CHUNKING_STRATEGY_VERSION,
            )

        return len(chunks)
