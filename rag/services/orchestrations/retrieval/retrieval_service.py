"""Retrieval service — owns the hybrid search pipeline end to end.

    query -> embed -> [RetrievalStrategy, ...] -> RankFusionStrategy
          -> [ResultFilter, ...] -> top_k

Every stage is injected, so the shape above is fixed but each stage's
behaviour is swappable. Today exactly one strategy (dense) is wired and
fusion is a pass-through; LexicalStrategy and reranking are seams, not
placeholders — see strategies/fusion.py and strategies/filters.py.

Depends directly on IEmbeddingModelService plus the already-built strategies/
fusion pipeline stages (audit M7 moved DenseVectorStrategy construction, and
the IChunkRepositoryService dependency it needs, to the composition root --
this service never called that Foundation service itself).

Split into a base logic file plus Validations/Exceptions mixins (this file,
retrieval_service_validations.py, retrieval_service_exceptions.py) -- mirrors
C#'s `partial class` merging EntitlementCodesOrchestrationService.cs /
.Validations.cs / .Exeptions.cs into one class. As with LearnerProfileService
and MistakePatternService, the concrete class is declared directly in THIS
file, inheriting the other two mixins by name -- no separate "_Base"
intermediate class, no composition step in __init__.py. (The previous
`_HybridRetrievalOrchestrationServiceBase` + __init__.py composition step was
the invented-`_ServiceBase` pattern CLAUDE.md explicitly disallows --
removed.)

Public methods are the ONLY thing that wraps with `_try_catch` (defined in
the Exceptions mixin) -- mirrors EntitlementCodesOrchestrationService.cs:
36-65's `RedeemEntitlementCodeForUserAsync(...) => TryCatch(async () =>
{...})`: the public `retrieve` method's entire body -- validate, then run
the pipeline -- is an inline nested closure passed straight to `_try_catch`,
not a separate `_retrieve` private method. No local try/except inside the
closure: every exception -- domain leaf, dependency, or otherwise --
propagates untouched to `_try_catch`, the single dispatch point that
classifies and wraps.

No Validation exception tier beyond the leaf itself is invented here --
retrieve()'s two input checks (blank query, top_k < 1) still raise the typed
RetrievalValidationError leaf from retrieval_service_validations.py, wrapped
by `_try_catch` exactly as before H5 of the architecture conformance audit.
"""

from typing import List, Optional, Sequence

from rag.brokers.logging import LoggingBroker
from rag.models.orchestrations.retrieval import ScoredChunk
from rag.services.foundations.embedding_model import IEmbeddingModelService
from rag.services.orchestrations.retrieval.i_retrieval_service import RetrievalService
from rag.services.orchestrations.retrieval.retrieval_service_exceptions import (
    HybridRetrievalOrchestrationServiceExceptions,
)
from rag.services.orchestrations.retrieval.retrieval_service_validations import (
    HybridRetrievalOrchestrationServiceValidations,
)
from rag.services.orchestrations.retrieval.strategies.dense import RetrievalStrategy
from rag.services.orchestrations.retrieval.strategies.filters import CategoryBoostFilter, ResultFilter
from rag.services.orchestrations.retrieval.strategies.fusion import RankFusionStrategy
from rag.services.orchestrations.retrieval.strategies.lexical import TextRetrievalStrategy


class HybridRetrievalOrchestrationService(
    HybridRetrievalOrchestrationServiceExceptions,
    HybridRetrievalOrchestrationServiceValidations,
    RetrievalService,
):
    """Finds the corpus chunks that ground a Review Mode explanation.

    Direct dependencies are the EmbeddingModel Foundation service (query
    embedding) plus the pipeline stages it composes. Strategies/fusion are
    built at the composition root (audit M7) — this service no longer
    constructs a default pipeline or accepts a ChunkRepository dependency
    it never calls itself.
    """

    def __init__(
        self,
        embedding_model_service: IEmbeddingModelService,
        strategies: Sequence[RetrievalStrategy],
        fusion: RankFusionStrategy,
        *,
        filters: Optional[Sequence[ResultFilter]] = None,
        alternate_strategy: Optional[TextRetrievalStrategy] = None,
        logging_broker: LoggingBroker,
    ) -> None:
        self._embedding_model_service = embedding_model_service
        # Mirrors the `ILoggingBroker loggingBroker` constructor parameter on
        # EntitlementCodesOrchestrationService.cs:22-33.
        self._logging_broker = logging_broker
        self._strategies: Sequence[RetrievalStrategy] = strategies
        self._fusion: RankFusionStrategy = fusion
        self._filters: Sequence[ResultFilter] = filters if filters is not None else []
        # Second-opinion search path (lexical). Only used when retrieve() is
        # called with alternate=True; never part of the default pipeline.
        self._alternate_strategy = alternate_strategy

    def retrieve(
        self, query: str, top_k: int, category: Optional[str] = None, alternate: bool = False
    ) -> List[ScoredChunk]:
        """Return up to top_k chunks grounding `query`, best-first.

        Args:
            query: the search text — for Review Mode, the flag's corrected text.
            top_k: maximum chunks to return. Owned by the caller (env-configured
                at the edge), never defaulted here.
            category: optional known-good topic hint (a flag's category). When
                given, chunks whose topic matches are floated to the front.
            alternate: when True, search with the alternate (lexical) strategy
                instead of the default dense pipeline -- the second-opinion
                pass. Skips embedding, fusion and the configured filters
                (those are distance-based; lexical scores are not distances);
                the category boost still applies. Returns [] when no alternate
                strategy is configured.

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

        def action() -> List[ScoredChunk]:
            self._validate_retrieve_input(query, top_k)

            # Query text at DEBUG only (user speech); ids and counts at INFO.
            self._logging_broker.log_debug(
                "retrieve query=%r top_k=%d category=%r", query, top_k, category
            )

            if alternate:
                if self._alternate_strategy is None:
                    self._logging_broker.log_info("alternate retrieval requested but none configured")
                    return []
                alt_results = self._alternate_strategy.search_text(query, top_k)
                if category is not None:
                    alt_results = CategoryBoostFilter(category, logging_broker=self._logging_broker).apply(alt_results)
                alt_results = alt_results[:top_k]
                self._logging_broker.log_info(
                    "retrieve alternate top_k=%d category=%r returned=%d ids=%s",
                    top_k,
                    category,
                    len(alt_results),
                    [chunk.chunk_id for chunk in alt_results],
                )
                return alt_results

            # No try/except: EmbeddingModelService.embed() already raises its
            # own wrapped EmbeddingModelDependencyException, which
            # _try_catch catches.
            query_embedding = self._embedding_model_service.embed([query])[0]

            # ponytail: each strategy is asked for exactly top_k, so a chunk
            # the category boost would have floated to rank 1 is invisible
            # if dense search ranked it top_k+1. Fine at MVP scale (3-5
            # topics, ~30 chunks). Upgrade path if Review Mode explanations
            # cite the wrong page: over-fetch here (top_k * a small factor)
            # and keep the final [:top_k] slice below exactly as it is.
            # No try/except here either: this chain bottoms out in
            # ChunkRepositoryService.search_by_vector(), which raises its own
            # wrapped ChunkRepositoryDependencyException for _try_catch to
            # catch.
            candidate_lists = [strategy.search(query_embedding, top_k) for strategy in self._strategies]

            fused = self._fusion.fuse(candidate_lists)

            # Cheap mismatch detection: if any chunk was ingested with a
            # different embedding model than the one currently configured,
            # log a warning. This is read-only signal (not an error), but
            # flags potential stale corpus issues for the user to
            # investigate. ponytail: a single log line, not a new validation
            # layer.
            configured_model = self._embedding_model_service.model_name
            mismatched = [
                c for c in fused if c.embedding_model_version and c.embedding_model_version != configured_model
            ]
            if mismatched:
                self._logging_broker.log_warning(
                    "embedding_model mismatch: configured=%r found_in_corpus=%s",
                    configured_model,
                    set(c.embedding_model_version for c in mismatched),
                )

            # Configured filters first, then the per-call category boost —
            # the caller's hint for this specific query gets the final say
            # on order. CategoryBoostFilter is built per call rather than
            # mutated, so no stage carries request state between calls.
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

        return self._try_catch(action)
