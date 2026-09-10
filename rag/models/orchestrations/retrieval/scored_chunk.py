"""Shared retrieval result type.

One dataclass used end-to-end: ChunkRepositoryBroker.search_by_vector returns
it, Retrieval's strategies/fusion/filters transform it, Generation and Review
consume it. Pinned in the Phase 2 architecture decision record — do not
narrow it or split it into a separate broker-only type.

Moved here from the flat `rag/models/retrieval.py` so an `exceptions/`
subpackage can sit beside it, mirroring
NL.Core.Entitlements.Api/Models/Foundations/Entitlements/Entitlement.cs
living alongside .../Entitlements/Exceptions/ — and the same treatment
`api/models/foundations/session_lifecycle/session_status.py` already got in this
codebase (data model in its own module, re-exported from the package
`__init__.py`).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ScoredChunk:
    chunk_id: int
    topic: str
    source_url: str
    content: str
    score: float
    embedding_model_version: Optional[str] = None
    chunking_strategy_version: Optional[str] = None
