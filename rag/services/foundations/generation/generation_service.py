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

Grounding check (Tri-Nature gap analysis, 2026-08-29, GAP 1 -- "No Judge on
Generation"): after the broker produces a draft explanation, a second call
to the same broker asks it to judge whether the draft is actually supported
by the retrieved chunk's content. A "not grounded" verdict is routed through
the exact same except-GenerationError fallback path as a broker failure --
one boolean decision, no new fallback mechanism, no scoring/threshold
config. Review Mode only; never called from Conversation Mode's live path.

Prompt templates (Tri-Nature gap analysis GAP 2 -- "Skills live in code, not
Data") live as plain text files under rag/data/prompts/, loaded once at
import time and filled in with str.format().

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
from pathlib import Path

import rag
from rag.brokers.generation import GenerationBroker, GenerationError
from rag.brokers.logging import LoggingBroker, StdlibLoggingBroker
from rag.models.generation import Explanation
from rag.models.retrieval import ScoredChunk
from rag.services.foundations.generation.i_generation_service import FlagLike

logger = logging.getLogger(__name__)

# ponytail: plain read_text() at import time, no templating framework --
# see GAP 2 above.
_PROMPTS_DIR = Path(rag.__file__).parent / "data" / "prompts"
_EXPLANATION_PROMPT = (_PROMPTS_DIR / "explanation.txt").read_text(encoding="utf-8")
_GROUNDING_JUDGE_PROMPT = (_PROMPTS_DIR / "grounding_judge.txt").read_text(encoding="utf-8")


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
            if not self._is_grounded(text, chunk):
                raise GenerationError("draft explanation failed the grounding check")
        except GenerationError as e:
            # Load-bearing log: this is the only signal distinguishing "Gemini
            # failed" from Review's own "no corpus match" fallback (same string,
            # api/services/review.py) — without it the two failure modes are
            # indistinguishable from logs alone.
            logger.info("generation failed, using fallback: %s", e)
            # Phase 1's exact fallback string, review/review.py:107 — preserve verbatim
            text = "I'm not certain on that one."
        return Explanation(explanation=text, source_url=chunk.source_url)

    def _is_grounded(self, explanation: str, chunk: ScoredChunk) -> bool:
        """Reflective judge (Ch.8): a second call to the same LLM reconsiders
        the draft before it can reach the user framed as "grounded, sourced".
        A broker failure on the judge call itself is treated as "not
        grounded" -- can't verify, so don't trust it.
        """
        judge_prompt = self._build_judge_prompt(explanation, chunk)
        try:
            verdict = self._broker.generate(judge_prompt)
        except GenerationError:
            return False
        return verdict.strip().upper().startswith("YES")

    def _build_prompt(self, flag: FlagLike, chunk: ScoredChunk) -> str:
        return _EXPLANATION_PROMPT.format(
            said=flag.said,
            corrected=flag.corrected,
            category=flag.category,
            content=chunk.content,
        )

    def _build_judge_prompt(self, explanation: str, chunk: ScoredChunk) -> str:
        return _GROUNDING_JUDGE_PROMPT.format(explanation=explanation, content=chunk.content)
