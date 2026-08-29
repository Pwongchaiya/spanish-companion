"""Foundation-layer service for the Generation feature.

Single broker dependency (GenerationBroker) — no waiver needed. Exception
surface is exactly one class, GenerationError, defined in
rag/brokers/generation.py; this service catches it and substitutes Phase 1's
fallback string instead of mapping it into a local exception hierarchy (see
CLAUDE.md's Foundation waiver for Generation).
"""

import logging
from typing import Protocol

from rag.brokers.generation import GenerationBroker, GenerationError
from rag.models.generation import Explanation
from rag.models.retrieval import ScoredChunk

logger = logging.getLogger(__name__)


class FlagLike(Protocol):
    """Local Protocol — do NOT import api.models.flag.Flag here. rag must
    never import from api (one-directional dependency: api -> rag). Flag
    (in api/models/flag.py) satisfies this structurally, no import needed.
    """

    said: str
    corrected: str
    category: str


class GenerationService:
    def __init__(self, broker: GenerationBroker) -> None:
        self._broker = broker

    def explain(self, flag: FlagLike, chunk: ScoredChunk) -> Explanation:
        prompt = self._build_prompt(flag, chunk)
        try:
            text = self._broker.generate(prompt)
        except GenerationError as e:
            # Load-bearing log: this is the only signal distinguishing "Gemini
            # failed" from Review's own "no corpus match" fallback (same string,
            # api/services/review.py) — without it the two failure modes are
            # indistinguishable from logs alone.
            logger.info("generation failed, using fallback: %s", e)
            # Phase 1's exact fallback string, review/review.py:107 — preserve verbatim
            text = "I'm not certain on that one."
        return Explanation(explanation=text, source_url=chunk.source_url)

    def _build_prompt(self, flag: FlagLike, chunk: ScoredChunk) -> str:
        return (
            f"A Spanish learner made this grammar mistake:\n"
            f"- They said: {flag.said!r}\n"
            f"- They meant: {flag.corrected!r}\n"
            f"- Category: {flag.category}\n\n"
            f"Here is relevant grammar content from the RAE (Royal Spanish Academy):\n"
            f"{chunk.content}\n\n"
            f"Write a short, warm, encouraging explanation (2-3 sentences) of the "
            f"correction, grounded in the grammar content above. Explain why the "
            f"corrected form is right and what the learner confused. Keep it friendly "
            f"and supportive, suitable for display as text on a review screen."
        )
