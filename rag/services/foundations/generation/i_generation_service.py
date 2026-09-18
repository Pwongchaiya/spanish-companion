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

    def judge_practice_attempt(self, flag: FlagLike, attempt_text: str) -> bool:
        """Return True if `attempt_text` correctly applies flag's correction.

        LearnerProfile Phase 2 (see decisions/dynamic-bot-behavior-and-
        learner-memory.md): one broker call, same shape as explain()'s
        grounding judge -- a single YES/NO verdict, no scoring/threshold
        config. Review Mode only, untimed. A broker failure is treated as
        "not mastered" (can't verify, so don't credit it) rather than
        raising -- same swallow-to-fallback shape as the grounding judge.
        May raise GenerationServiceException for anything else unexpected.
        """
        ...
