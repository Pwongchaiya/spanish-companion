"""Retrieval service — owns the hybrid search pipeline end to end.

    query -> embed -> [RetrievalStrategy, ...] -> RankFusionStrategy
          -> [ResultFilter, ...] -> top_k

Every stage is injected, so the shape above is fixed but each stage's
behaviour is swappable. Today exactly one strategy (dense) is wired and
fusion is a pass-through; LexicalStrategy and reranking are seams, not
placeholders — see strategies/fusion.py and strategies/filters.py.

Depends on exactly two Foundation services -- IEmbeddingModelService and
IChunkRepositoryService -- so the Florance Pattern (ORC-001, 2-3 deps) and
ORC-002 (no direct broker deps) are both satisfied outright; the CLAUDE.md
Phase 2 waiver that previously covered this service's raw-broker deps no
longer needs to apply to it.

Split into this base logic file plus an Exceptions mixin
(retrieval_service_exceptions.py), combined into the concrete
HybridRetrievalService in __init__.py -- mirrors C#'s `partial class`
merging EntitlementCodesOrchestrationService.cs /
EntitlementCodesOrchestrationService.Exeptions.cs into one class, the same
multi-inheritance-merge already used for Session Lifecycle and Review in
this codebase.

Input checks live in retrieval_service_validations.py, mirroring the
reference's EntitlementCodesOrchestrationService.Validations.cs. They used to
be inline in retrieve() and raise a bare ValueError from outside _try_catch;
H5 of the architecture conformance audit replaced that with the typed
RetrievalValidationError leaf, wrapped like every other failure this service
can produce.
"""

from typing import List, Optional, Sequence

from rag.brokers.logging import LoggingBroker, StdlibLoggingBroker
from rag.models.retrieval import ScoredChunk
from rag.services.foundations.chunk_repository import IChunkRepositoryService
from rag.services.foundations.embedding_model import IEmbeddingModelService
from rag.services.orchestrations.retrieval.strategies.dense import DenseVectorStrategy, RetrievalStrategy
from rag.services.orchestrations.retrieval.strategies.filters import CategoryBoostFilter, ResultFilter
from rag.services.orchestrations.retrieval.strategies.fusion import PassThroughRankFusion, RankFusionStrategy


class _HybridRetrievalServiceBase:
    """Finds the corpus chunks that ground a Review Mode explanation.

    Direct dependencies are the EmbeddingModel Foundation service (query
    embedding) plus the pipeline stages it composes. The ChunkRepository
    Foundation service is passed in only to build the default
    DenseVectorStrategy — that strategy owns it, and this service never
    calls it.

    The public `retrieve` delegates to a private `_retrieve` through
    `_try_catch` (defined in the Exceptions mixin), mirroring
    EntitlementCodesOrchestrationService.cs:36-65's
    `RedeemEntitlementCodeForUserAsync(...) => TryCatch(async () => {...})`.
    """

    def __init__(
        self,
        embedding_model_service: IEmbeddingModelService,
        chunk_repository_service: IChunkRepositoryService,
        strategies: Optional[Sequence[RetrievalStrategy]] = None,
        fusion: Optional[RankFusionStrategy] = None,
        filters: Optional[Sequence[ResultFilter]] = None,
        logging_broker: LoggingBroker = StdlibLoggingBroker(),
    ) -> None:
        self._embedding_model_service = embedding_model_service
        # Mirrors the `ILoggingBroker loggingBroker` constructor parameter on
        # EntitlementCodesOrchestrationService.cs:22-33.
        self._logging_broker = logging_broker
        # Defaults are the whole MVP pipeline, so app.py wires two Foundation
        # services and is done — no caller has to assemble stages by hand to
        # get the behaviour everything currently expects.
        self._strategies: Sequence[RetrievalStrategy] = (
            strategies
            if strategies is not None
            else [DenseVectorStrategy(chunk_repository_service, logging_broker=self._logging_broker)]
        )
        self._fusion: RankFusionStrategy = (
            fusion if fusion is not None else PassThroughRankFusion(logging_broker=self._logging_broker)
        )
        self._filters: Sequence[ResultFilter] = filters if filters is not None else []

    def retrieve(self, query: str, top_k: int, category: Optional[str] = None) -> List[ScoredChunk]:
        """Return up to top_k chunks grounding `query`, best-first.

        Args:
            query: the search text — for Review Mode, the flag's corrected text.
            top_k: maximum chunks to return. Owned by the caller (env-configured
                at the edge), never defaulted here.
            category: optional known-good topic hint (a flag's category). When
                given, chunks whose topic matches are floated to the front.

        Returns:
            Up to top_k chunks, or [] when the corpus has no match. Empty is a
            valid result, not an error — Review short-circuits on it before
            calling Generation.

        Raises:
            RetrievalOrchestrationValidationException: wrapping
                RetrievalValidationError — blank query, or top_k < 1.
            RetrievalOrchestrationDependencyException: wrapping
                EmbeddingModelDependencyException or
                ChunkRepositoryDependencyException — the Foundation service
                beneath reported its broker unreachable.
            RetrievalOrchestrationServiceException: anything else.
        """
        # Inside _try_catch, mirroring EntitlementCodesOrchestrationService.cs:36-65
        # where ValidateEntitlementCodeInputOnRedeem is the first statement of
        # the TryCatch delegate — so the leaf is wrapped and logged on its way
        # out like every other failure here.
        def _validated_retrieve() -> List[ScoredChunk]:
            self._validate_retrieve_input(query, top_k)
            return self._retrieve(query, top_k, category)

        return self._try_catch(_validated_retrieve)

    def _retrieve(self, query: str, top_k: int, category: Optional[str]) -> List[ScoredChunk]:
        # Query text at DEBUG only (user speech); ids and counts at INFO.
        self._logging_broker.log_debug("retrieve query=%r top_k=%d category=%r", query, top_k, category)

        # No try/except: EmbeddingModelService.embed() already raises its own
        # wrapped EmbeddingModelDependencyException, which _try_catch catches.
        query_embedding = self._embedding_model_service.embed([query])[0]

        # ponytail: each strategy is asked for exactly top_k, so a chunk the
        # category boost would have floated to rank 1 is invisible if dense
        # search ranked it top_k+1. Fine at MVP scale (3-5 topics, ~30
        # chunks). Upgrade path if Review Mode explanations cite the wrong
        # page: over-fetch here (top_k * a small factor) and keep the final
        # [:top_k] slice below exactly as it is.
        # No try/except here either: this chain bottoms out in
        # ChunkRepositoryService.search_by_vector(), which raises its own
        # wrapped ChunkRepositoryDependencyException for _try_catch to catch.
        candidate_lists = [strategy.search(query_embedding, top_k) for strategy in self._strategies]

        fused = self._fusion.fuse(candidate_lists)

        # Cheap mismatch detection: if any chunk was ingested with a different
        # embedding model than the one currently configured, log a warning. This
        # is read-only signal (not an error), but flags potential stale corpus
        # issues for the user to investigate. ponytail: a single log line, not a
        # new validation layer.
        configured_model = self._embedding_model_service.model_name
        mismatched = [c for c in fused if c.embedding_model_version and c.embedding_model_version != configured_model]
        if mismatched:
            self._logging_broker.log_warning(
                "embedding_model mismatch: configured=%r found_in_corpus=%s",
                configured_model,
                set(c.embedding_model_version for c in mismatched),
            )

        # Configured filters first, then the per-call category boost — the
        # caller's hint for this specific query gets the final say on order.
        # CategoryBoostFilter is built per call rather than mutated, so no
        # stage carries request state between calls.
        pipeline: List[ResultFilter] = list(self._filters)
        if category is not None:
            pipeline.append(CategoryBoostFilter(category, logging_broker=self._logging_broker))

        for result_filter in pipeline:
            fused = result_filter.apply(fused)

        results = fused[:top_k]
        self._logging_broker.log_info(
            "retrieve top_k=%d category=%r returned=%d ids=%s",
            top_k,
            category,
            len(results),
            [chunk.chunk_id for chunk in results],
        )
        return results
