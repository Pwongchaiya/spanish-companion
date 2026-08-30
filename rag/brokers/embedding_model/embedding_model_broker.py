"""Broker for the sentence-transformers embedding model.

Phase 1 loaded a SentenceTransformer independently in rag/ingest.py and
rag/retrieve.py, kept in sync only by a "must match" comment. This broker is
the single source of truth: one model instance, loaded lazily on first use
and reused for every call after that, whether the caller is Ingestion
(batches of chunk texts) or Retrieval (a single-element query list).

No DB, no SQLAlchemy — the model itself is the only external resource here.
"""

import os
from functools import cached_property
from typing import List, Optional

from sentence_transformers import SentenceTransformer

# Matches rag/ingest.py's and rag/retrieve.py's existing default exactly —
# multilingual model, 384-dim output. BGE-small-en was tried and dropped
# (English-only, couldn't embed Spanish queries); see CLAUDE.md tech stack.
_DEFAULT_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class SentenceTransformerEmbeddingModelBroker:
    """EmbeddingModelBroker backed by a local sentence-transformers model.

    `model_name` defaults to EMBEDDING_MODEL_NAME (env), then the project's
    pinned multilingual default — same defaulting shape as
    api/brokers/bot_process/bot_process_broker.py's `command`/`cwd`.
    """

    def __init__(self, model_name: Optional[str] = None) -> None:
        env_model_name = os.getenv("EMBEDDING_MODEL_NAME", _DEFAULT_MODEL_NAME)
        self._model_name = model_name if model_name is not None else env_model_name

    @property
    def model_name(self) -> str:
        """The model name this broker is configured to use."""
        return self._model_name

    @cached_property
    def _model(self) -> SentenceTransformer:
        # ponytail: cached_property gives lazy-load-once-reuse for free,
        # no explicit if-is-None-then-load guard needed.
        return SentenceTransformer(self._model_name)

    def embed(self, texts: List[str]) -> List[List[float]]:
        return self._model.encode(texts, convert_to_tensor=False).tolist()
