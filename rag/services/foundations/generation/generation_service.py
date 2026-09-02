"""Base logic for GenerationService.

Foundation-tier per CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers:
single broker dependency (GenerationBroker), no waiver needed. Exception
surface is exactly one broker-level class, GenerationError (defined in
rag/brokers/generation/i_generation_broker.py); this service catches it and
substitutes Phase 1's fallback string instead of mapping it into a local
exception hierarchy -- a deliberate, already-verified business decision
(see Review's own decision record tracing Generation's exception
plumbing). That swallow-to-fallback behavior is unchanged here, just
relocated.

Split into this base logic file plus an Exceptions mixin
(generation_service_exceptions.py), combined into the concrete
GenerationService in __init__.py -- mirrors C#'s `partial class` merging
EntitlementService.cs / .Exeptions.cs into one class
(python-adaptations-skill.md's Architecture Patterns table), the same
multi-inheritance-merge pattern api/services/session_lifecycle/ already
uses. No Validations mixin here (unlike Session Lifecycle) -- there is no
existing business rule requiring blank flag/chunk fields to be rejected,
and inventing one now would be new business logic, not a citation-driven
restructuring.
"""

import logging

from rag.brokers.generation import GenerationBroker, GenerationError
from rag.brokers.logging import LoggingBroker, StdlibLoggingBroker
from rag.models.generation import Explanation
from rag.models.retrieval import ScoredChunk
from rag.services.foundations.generation.i_generation_service import FlagLike

logger = logging.getLogger(__name__)


class _GenerationServiceBase:
    """Owns explain()'s prompt-building + broker call + fallback logic.

    The public method delegates through `_try_catch` (defined in the
    Exceptions mixin) per python-adaptations-skill.md's TryCatch
    translation -- mirrors EntitlementService.cs:31-41.
    """

    def __init__(
        self,
        broker: GenerationBroker,
        logging_broker: LoggingBroker = StdlibLoggingBroker(),
    ) -> None:
        self._broker = broker
        self._logging_broker = logging_broker

    def explain(self, flag: FlagLike, chunk: ScoredChunk) -> Explanation:
        return self._try_catch(lambda: self._explain(flag, chunk))

    def _explain(self, flag: FlagLike, chunk: ScoredChunk) -> Explanation:
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
