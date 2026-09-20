"""Interface for the Generation feature's Foundation-tier service.

Mirrors NL.Core.Entitlements.Api/Services/Foundations/Entitlements/
IEntitlementService.cs:12-19 -- typing.Protocol, not abc.ABC, per this
project's broker-interface waiver (CLAUDE.md's Phase 2 Layer-Agent Mapping
& Waivers table), extended to service interfaces the same way Session
Lifecycle's api/services/session_lifecycle/i_session_lifecycle_service.py
already does: the reference project itself co-locates the interface file
with its implementation, same folder.

Named IGenerationService rather than the bare "GenerationService" the
reference's IEntitlementService/EntitlementService pairing would otherwise
suggest, because this feature's concrete composed class keeps its
pre-existing name `GenerationService` -- every current consumer
(rag/controllers/generation.py, api/app.py, the existing test suite) already
imports/constructs it under that exact name, and renaming it would break
call sites this rebuild is not supposed to touch (see CLAUDE.md dispatch:
"keep the class name"). Session Lifecycle sidestepped the same collision
from the other side, by giving its *concrete* class a different, more
specific name (ConversationSessionService) than its interface
(SessionLifecycleService); here the collision is resolved on the interface
side instead.
"""

from typing import Protocol

from rag.models.foundations.generation import Explanation
from rag.models.orchestrations.retrieval import ScoredChunk


class FlagLike(Protocol):
    """Local Protocol — do NOT import api.models.foundations.flag.Flag here. rag must
    never import from api (one-directional dependency: api -> rag). Flag
    (in api/models/flag.py) satisfies this structurally, no import needed.
    """

    said: str
    corrected: str
    category: str


class IGenerationService(Protocol):
    """External-facing contract for Generation's Foundation-tier service."""

    def explain(self, flag: FlagLike, chunk: ScoredChunk) -> Explanation:
        """Return a grounded explanation for `flag` using `chunk`'s content.

        A second broker call judges whether the draft explanation is
        actually supported by `chunk`'s content before it is returned
        (Review Mode only -- untimed, budgeted for the extra call). Never
        raises GenerationError -- a broker failure, or a "not grounded"
        verdict, is caught and replaced with a fixed fallback string. May
        raise GenerationServiceException for anything else unexpected.
        """
        ...

    def judge_practice_attempt(self, flag: FlagLike, attempt_text: str, roleplay_setting: str | None = None) -> str:
        """Return one of "again" | "hard" | "good" | "easy" grading how well
        `attempt_text` applies flag's correction.

        LearnerProfile Phase 2 (see decisions/dynamic-bot-behavior-and-
        learner-memory.md), A2 (graded verdict): one broker call, same shape
        as explain()'s grounding judge, now returning an Anki-style 4-level
        grade instead of a binary YES/NO verdict. Review Mode only, untimed.
        A broker failure, or a response that doesn't parse to one of the four
        grades, falls back to "again" (can't verify, so don't credit it) --
        same swallow-to-fallback shape as the grounding judge. Deriving the
        `mastered: bool` other consumers rely on (`grade in ("good", "easy")`)
        is Review's job, not this service's -- see
        ReviewOrchestrationService.record_practice(). May raise
        GenerationServiceException for anything else unexpected.

        `roleplay_setting` (LearnerProfile Phase 4, optional) frames the
        judged attempt inside a roleplay scene instead of a bare sentence --
        resolved from a known slug by Review, api-side; this layer only ever
        sees the resolved text, never a slug (rag must not import api/data).
        """
        ...

    def judge_task_outcome(self, transcript_text: str, success_condition: str) -> str | None:
        """Judge whether a session transcript met a task scenario's
        `success_condition` (roadmap D4). Returns "success" or "fail", or
        None -- never raises past this method for a broker failure or an
        unparseable verdict -- meaning "couldn't judge", which the caller must
        treat as leave-unjudged rather than persist a guess. Same swallow-to-
        None shape as estimate_cefr_level(). Review Mode only, untimed; the
        condition arrives as resolved text (rag must not import api/data).
        May raise GenerationServiceException for anything else unexpected.
        """
        ...

    def estimate_cefr_level(self, transcript_text: str) -> str | None:
        """Estimate a CEFR level (A1-C2) from a full session transcript.

        Roadmap A6, async/best-effort from Voice Conversation's teardown
        path. Returns None -- never raises past this method for a broker
        failure or an unparseable verdict -- meaning "couldn't estimate this
        session"; the caller must treat None as skip-the-update, never write
        a garbage value to learner_profile.cefr_estimate. Same swallow-to-
        None shape as explain()'s grounding judge and
        judge_practice_attempt()'s swallow-to-False, just with a third
        outcome (parsed level) instead of two.
        May raise GenerationServiceException for anything else unexpected.
        """
        ...

    def generate_text(self, prompt: str) -> str | None:
        """Run a caller-built prompt (api owns its text; rag must not import
        api/data) and return the stripped answer, or None when the broker
        fails or answers empty -- never raises GenerationError. Best-effort,
        for teardown work such as the persona memory summary."""
        ...
