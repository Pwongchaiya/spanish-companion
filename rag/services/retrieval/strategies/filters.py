"""Result filters — the post-fusion stage of hybrid search.

A filter takes the fused ranking and returns a ranking: it may reorder, drop,
or pass through, but it never invents chunks. Filters run in the order the
service holds them, each one seeing the previous one's output.

Reranking is a deferred seam, not built here. When it lands it is a
ResultFilter like any other — a cross-encoder needs the query text, which it
gets the same way CategoryBoostFilter gets its category: constructed per
call with it. The Protocol below does not change.
"""

import logging
import re
from typing import List, Optional, Protocol

from rag.models.retrieval import ScoredChunk

logger = logging.getLogger(__name__)


def _normalize(text: str) -> str:
    """Lowercase, punctuation-to-space, single-spaced.

    Bridges the corpus's hyphenated slugs ("ser-vs-estar", from rag/ingest.py's
    TOPICS) and the LLM's free-form flag categories ("ser vs estar", from
    voice/bot.py's system prompt) — two vocabularies that were never actually
    equal as raw strings.

    Splits on [\\W_] rather than [^a-z0-9] so Spanish accents survive: a
    category like "concordancia de género" normalizes to itself, not to
    "concordancia de g nero".
    """
    return re.sub(r"[\W_]+", " ", text.casefold()).strip()


def _matches(topic: str, category: str) -> bool:
    """True when either normalized string contains the other, on word boundaries.

    Containment, not equality, because the two vocabularies are related but
    not identical even after normalization — the corpus topic
    "subjunctive-basics" is the right ground for the flag category
    "subjunctive".

    Space-padding makes containment word-boundary-safe, so the category "ser"
    matches the topic "ser vs estar" but not a topic like "insert".
    """
    padded_topic, padded_category = f" {topic} ", f" {category} "
    return padded_category in padded_topic or padded_topic in padded_category


class ResultFilter(Protocol):
    """One post-fusion transform over a ranked candidate list."""

    def apply(self, chunks: List[ScoredChunk]) -> List[ScoredChunk]:
        """Return the chunks reordered and/or narrowed, best-first.

        Anything the filter needs beyond the chunks themselves (a category, a
        query, a threshold) is constructor state — this signature stays
        one-argument so filters compose blindly.
        """
        ...


class CategoryBoostFilter:
    """Floats chunks whose `topic` matches a category to the front of the ranking.

    Generalizes the Phase 1 finding recorded in rag/retrieve.py: on a short
    Spanish example sentence (Review Mode's real query — the flag's corrected
    text) pure cosine similarity does not reliably rank the right topic
    first, even though an English topic label does. Review already knows the
    flag's `category`, which shares vocabulary with `ScoredChunk.topic`
    (e.g. "ser vs estar") per the architecture record — so that known-good
    signal is applied here instead of being thrown away.

    Boost mechanism: a **stable partition**, not a score adjustment. Chunks
    whose topic matches are moved ahead of those that don't; relative order
    within each group is left exactly as fusion ranked it, and no score is
    touched. Nothing is ever dropped — a non-matching chunk is still the best
    available answer when no chunk matches.

    Why partition rather than nudge the score: `score` semantics are not
    stable across this pipeline's roadmap. Today it is a pgvector cosine
    *distance* (lower = closer); once RRF replaces PassThroughRankFusion it
    becomes a fused rank score (higher = better). Any epsilon tuned against
    today's distances would silently invert into a penalty the day fusion
    lands. Reordering carries no such assumption, and the boost is
    monotone-safe either way.

    Matching is normalized word-boundary containment (see _normalize /
    _matches), NOT string equality. Equality was tried and is provably dead
    code in this repo: corpus topics are hyphenated slugs and flag categories
    are spaced free-form LLM output, so no pair is ever equal and the boost
    silently no-ops. Against the real vocabularies this rule fires on all
    three overlapping pairs — "ser-vs-estar"/"ser vs estar",
    "preterite-vs-imperfect"/"preterite vs imperfect",
    "subjunctive-basics"/"subjunctive" — and correctly declines to boost
    "gender agreement" and "vocabulary", which no corpus topic covers.

    # ponytail: containment on normalized tokens, not fuzzy or semantic
    # matching. Ceiling: an LLM category that shares no word with any topic
    # ("word choice" vs "vocabulary") won't match, and a boost is only ever
    # a reorder, so the cost of a miss is falling back to pure cosine — the
    # status quo, never worse. Upgrade path if categories drift further:
    # constrain voice/bot.py's prompt to emit a topic id from a fixed list,
    # which kills the vocabulary gap at the source rather than here.
    """

    def __init__(self, category: Optional[str] = None) -> None:
        # None means "no category known for this call" — pass-through, so the
        # caller never needs a conditional around this filter.
        self._category = _normalize(category) if category else None

    def apply(self, chunks: List[ScoredChunk]) -> List[ScoredChunk]:
        if not self._category:
            logger.debug("CategoryBoostFilter: no category, ranking unchanged")
            return chunks

        # Stable sort, False (match) before True (no match) — matching chunks
        # move to the front, everything keeps its fusion-relative order.
        boosted = sorted(chunks, key=lambda chunk: not _matches(_normalize(chunk.topic), self._category))

        matched = [chunk.chunk_id for chunk in boosted if _matches(_normalize(chunk.topic), self._category)]
        logger.debug(
            "CategoryBoostFilter category=%r boosted=%s (of %d, none dropped) order %s -> %s",
            self._category,
            matched,
            len(chunks),
            [chunk.chunk_id for chunk in chunks],
            [chunk.chunk_id for chunk in boosted],
        )
        return boosted
