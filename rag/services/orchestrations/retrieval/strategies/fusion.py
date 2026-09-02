"""Rank fusion — merges every strategy's candidate list into one ranking.

This is a real pipeline stage even though only one strategy exists today.
It takes a *list of ranked lists* (RRF's shape), not a single list, so
adding LexicalStrategy later changes only this stage's internals — never its
interface, and never the service that calls it.
"""

import logging
from typing import List, Protocol

from rag.models.retrieval import ScoredChunk

logger = logging.getLogger(__name__)


class RankFusionStrategy(Protocol):
    """Merges N ranked candidate lists into one ranked list."""

    def fuse(self, candidate_lists: List[List[ScoredChunk]]) -> List[ScoredChunk]:
        """Return one best-first ranked list merged from all inputs.

        Input lists are each best-first by their own strategy's native score.
        Those scores are NOT comparable across strategies (cosine distance vs
        a BM25 score), which is why the real implementation will fuse by
        rank position, not by score value.
        """
        ...


class PassThroughRankFusion:
    """Single-list pass-through: one strategy in, the same ranking out.

    # ponytail: with exactly one strategy wired, Reciprocal Rank Fusion
    # reduces to the identity — RRF over a single list produces
    # 1/(k+rank), which is strictly decreasing in rank and therefore
    # preserves the input order exactly. So the merge is a no-op today and
    # computing the RRF scores would only overwrite the useful cosine
    # distances with meaningless constants.
    #
    # Ceiling: two or more lists cannot be merged by this class and it says
    # so loudly rather than concatenating into a silently-wrong ranking.
    # Upgrade path, when LexicalStrategy lands: replace this class's body
    # with RRF proper — score(chunk) = sum over lists of 1/(k + rank),
    # k=60 from the Cormack et al. default, ranks 1-based, chunks keyed by
    # chunk_id — and overwrite ScoredChunk.score with that fused value
    # (which is then higher-is-better, flipping today's distance
    # semantics; CategoryBoostFilter is deliberately score-agnostic so it
    # survives that flip unchanged).
    """

    def fuse(self, candidate_lists: List[List[ScoredChunk]]) -> List[ScoredChunk]:
        if not candidate_lists:
            logger.debug("PassThroughRankFusion: no candidate lists, nothing to fuse")
            return []

        if len(candidate_lists) > 1:
            raise NotImplementedError(
                f"PassThroughRankFusion received {len(candidate_lists)} candidate lists; "
                "it can only pass a single list through. Implement Reciprocal Rank Fusion "
                "here before wiring a second RetrievalStrategy."
            )

        fused = candidate_lists[0]
        logger.debug(
            "PassThroughRankFusion: 1 list, %d candidates passed through unchanged (ids=%s)",
            len(fused),
            [chunk.chunk_id for chunk in fused],
        )
        return fused
