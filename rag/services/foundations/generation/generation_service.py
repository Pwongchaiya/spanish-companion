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

Split into this file plus an Exceptions mixin (generation_service_exceptions.py)
-- mirrors C#'s `partial class` merging EntitlementService.cs /
.Exeptions.cs into one class (python-adaptations-skill.md's Architecture
Patterns table). The concrete class is declared directly in THIS file,
inheriting the Exceptions mixin by name -- no separate "_Base" intermediate
class, no composition step in __init__.py (matches LearnerProfileService's
rebuilt shape; the previous `_GenerationServiceBase` + __init__.py
composition step was the invented-`_ServiceBase` pattern CLAUDE.md
explicitly disallows -- removed). No Validations mixin here (unlike Session
Lifecycle) -- there is no existing business rule requiring blank
flag/chunk fields to be rejected, and inventing one now would be new
business logic, not a citation-driven restructuring.

explain() wraps its entire body -- prompt build, broker call, grounding
check, fallback -- in a single inline nested closure passed straight to
`_try_catch`, matching LearnerProfileService's shape. No local try/except
inside the closure: the except-GenerationError-fallback and the grounding
check are unchanged business logic, not exception handling that competes
with `_try_catch` -- both stay exactly where they were, just no longer
behind a separate `_do_thing` indirection layer.
"""

from pathlib import Path

import rag
from rag.brokers.generation import GenerationBroker, GenerationError
from rag.brokers.logging import LoggingBroker
from rag.models.foundations.generation import Explanation
from rag.models.orchestrations.retrieval import ScoredChunk
from rag.services.foundations.generation.generation_service_exceptions import (
    GenerationServiceExceptions,
)
from rag.services.foundations.generation.i_generation_service import FlagLike, IGenerationService

# ponytail: plain read_text() at import time, no templating framework --
# see GAP 2 above.
_PROMPTS_DIR = Path(rag.__file__).parent / "data" / "prompts"
_EXPLANATION_PROMPT = (_PROMPTS_DIR / "explanation.txt").read_text(encoding="utf-8")
_GROUNDING_JUDGE_PROMPT = (_PROMPTS_DIR / "grounding_judge.txt").read_text(encoding="utf-8")
_PRACTICE_JUDGE_PROMPT = (_PROMPTS_DIR / "practice_judge.txt").read_text(encoding="utf-8")


class GenerationService(GenerationServiceExceptions, IGenerationService):
    """Owns explain()'s prompt-building + broker call + fallback logic.

    The public method delegates its entire body through `_try_catch`
    (defined in the Exceptions mixin) per python-adaptations-skill.md's
    TryCatch translation -- mirrors EntitlementService.cs:31-41 and
    LearnerProfileService's rebuilt shape.
    """

    def __init__(
        self,
        broker: GenerationBroker,
        *,
        logging_broker: LoggingBroker,
    ) -> None:
        self._broker = broker
        self._logging_broker = logging_broker

    def explain(self, flag: FlagLike, chunk: ScoredChunk) -> Explanation:
        def action() -> Explanation:
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
                self._logging_broker.log_info("generation failed, using fallback: %s", e)
                # Phase 1's exact fallback string, review/review.py:107 — preserve verbatim
                text = "I'm not certain on that one."
            return Explanation(explanation=text, source_url=chunk.source_url, source_excerpt=chunk.content)

        return self._try_catch(action)

    def judge_practice_attempt(self, flag: FlagLike, attempt_text: str) -> bool:
        def action() -> bool:
            prompt = self._build_practice_judge_prompt(flag, attempt_text)
            try:
                verdict = self._broker.generate(prompt)
            except GenerationError as e:
                self._logging_broker.log_info("practice judge call failed, treating as not mastered: %s", e)
                return False
            mastered = verdict.strip().upper().startswith("YES")
            self._logging_broker.log_info(
                "practice judge verdict for category=%s: %s", flag.category, verdict.strip()
            )
            return mastered

        return self._try_catch(action)

    def _build_practice_judge_prompt(self, flag: FlagLike, attempt_text: str) -> str:
        return _PRACTICE_JUDGE_PROMPT.format(
            said=flag.said,
            corrected=flag.corrected,
            category=flag.category,
            attempt=attempt_text,
        )

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
        grounded = verdict.strip().upper().startswith("YES")
        if not grounded:
            self._logging_broker.log_info("grounding judge verdict: %s", verdict.strip())
        return grounded

    def _build_prompt(self, flag: FlagLike, chunk: ScoredChunk) -> str:
        return _EXPLANATION_PROMPT.format(
            said=flag.said,
            corrected=flag.corrected,
            category=flag.category,
            content=chunk.content,
        )

    def _build_judge_prompt(self, explanation: str, chunk: ScoredChunk) -> str:
        return _GROUNDING_JUDGE_PROMPT.format(explanation=explanation, content=chunk.content)
