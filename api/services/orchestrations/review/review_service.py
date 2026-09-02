"""Orchestration service for Review Mode.

Composes four service dependencies -- two api Foundation services
(FlagService, PracticeLogService) and two rag services (HybridRetrievalService,
GenerationService) -- into the Review Mode flow: flagged list -> selection ->
grounded explanation -> single practice attempt.

Composition, not reimplementation: flag lookup and practice-attempt
persistence live in api/services/foundations/, retrieval ranking lives in
rag/services/orchestrations/retrieval/, prompt-building and LLM-failure
fallback live in rag/services/foundations/generation/. What is genuinely
Review's own is here and only here: deciding what happens when the corpus has
no match.

Importing rag.services.* from api is the one deliberate package-boundary
crossing (api -> rag, never the reverse). The rag controllers that used to
sit between (RetrievalController / GenerationController) were pure
pass-throughs and are gone from this call path; the two rag dependencies are
typed concretely rather than via a Protocol, because there is no
cross-package service-interface convention established here.

Per CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers, ORC-001 (Florance
dep-count limit) is waived: this service coordinates four dependencies, not
two or three. ORC-002 no longer applies -- nothing here touches a broker
directly any more.

Split into a base logic file plus an Exceptions mixin (this file,
review_service_exceptions.py), combined into the concrete ReviewOrchestrator
in __init__.py -- mirrors C#'s `partial class` merging
EntitlementCodesOrchestrationService.cs / .Exeptions.cs into one class, the
same multi-inheritance-merge already used for Session Lifecycle in this
codebase. No Validations mixin: the one check that lived here
(blank attempt_text) now belongs to PracticeLogService, so nothing is
validated at this tier.
"""

import logging
import os
from datetime import datetime
from typing import Callable, List

from dotenv import load_dotenv

from api.brokers.logging import LoggingBroker, StdlibLoggingBroker
from api.brokers.practice_log import PracticeAttempt
from api.models.flag import Flag
from api.services.foundations.flag import IFlagService
from api.services.foundations.practice_log import IPracticeLogService
from rag.models.generation import Explanation
from rag.services.foundations.generation import GenerationService
from rag.services.orchestrations.retrieval import HybridRetrievalService

load_dotenv()

logger = logging.getLogger(__name__)

# ponytail: one knob -> plain os.getenv at import time, same pattern as
# api/services/session_lifecycle/ and rag/db.py (load_dotenv() then
# os.getenv with a string default, cast at the read site).
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "3"))


class _ReviewOrchestratorBase:
    """Owns Review Mode's flow across flags, retrieval, generation, practice.

    Public methods delegate to a private `_do_thing` method through
    `_try_catch` (defined in the Exceptions mixin), mirroring
    EntitlementCodesOrchestrationService.cs:36-65's
    `RedeemEntitlementCodeForUserAsync(...) => TryCatch(async () => {...})`.
    """

    def __init__(
        self,
        flag_service: IFlagService,
        practice_log_service: IPracticeLogService,
        retrieval_service: HybridRetrievalService,
        generation_service: GenerationService,
        clock: Callable[[], datetime] = datetime.now,
        logging_broker: LoggingBroker = StdlibLoggingBroker(),
    ) -> None:
        self._flag_service = flag_service
        self._practice_log_service = practice_log_service
        self._retrieval_service = retrieval_service
        self._generation_service = generation_service
        # Injected for the same reason session_lifecycle injects time_source:
        # CLAUDE.md's unit-test rule forbids live datetime.now().
        self._clock = clock
        # Mirrors the `ILoggingBroker loggingBroker` constructor parameter on
        # EntitlementCodesOrchestrationService.cs:22-33 -- every
        # _create_and_log_* method logs through it before raising.
        self._logging_broker = logging_broker

    def list_flags(self) -> List[Flag]:
        """The current flag list, for the UI's flagged-list -> selection step.

        Pass-through, deliberately NOT routed through _try_catch:
        FlagService.list_flags() is itself unwrapped for the same reason one
        layer down -- FlagBroker.load_flags() already returns [] for a
        missing or corrupt file, and "no flags yet" is a normal state, not an
        error. Same treatment as ConversationSessionService.get_status(),
        which is the one Session Lifecycle method left unwrapped for the same
        reason.
        """
        return self._flag_service.list_flags()

    def explain_flag(self, flag_id: str) -> Explanation:
        return self._try_catch(lambda: self._explain_flag(flag_id))

    def _explain_flag(self, flag_id: str) -> Explanation:
        flag = self._flag_service.get_flag(flag_id)

        chunks = self._retrieval_service.retrieve(
            query=flag.corrected,
            top_k=RETRIEVAL_TOP_K,
            category=flag.category,
        )
        if not chunks:
            # Review's problem, not Generation's: GenerationService.explain()
            # requires a real chunk (its contract has no Optional), so calling it
            # here would be a contract violation, not a graceful degradation.
            #
            # This log line is the ONLY thing distinguishing this failure mode
            # (corpus has nothing on the topic -> ingest more RAE pages) from
            # Generation's LLM failure (rag/services/generation.py:37-46 ->
            # retry), because both deliberately return the same user-facing
            # string.
            logger.info("no corpus match for flag_id=%s category=%r", flag_id, flag.category)
            # Phase 1's exact fallback string, review/review.py:107 — preserve
            # verbatim, same as GenerationService's. One user-facing "couldn't
            # help with this" string across the system; debugging splits them in
            # the logs above, not in the copy.
            return Explanation(explanation="I'm not certain on that one.", source_url="")

        # retrieve() returns best-first, so [0] is the top-ranked chunk.
        return self._generation_service.explain(flag, chunks[0])

    def record_practice(self, flag_id: str, attempt_text: str) -> PracticeAttempt:
        return self._try_catch(lambda: self._record_practice(flag_id, attempt_text))

    def _record_practice(self, flag_id: str, attempt_text: str) -> PracticeAttempt:
        # Look the flag up purely to reject unknown ids -- same not-found
        # handling as explain_flag. A practice attempt against a flag that
        # isn't in the list is a client-side state mismatch worth surfacing,
        # not an orphan row worth writing.
        #
        # Lookup runs BEFORE PracticeLogService.record_attempt()'s blank-text
        # check, so an unknown flag_id wins when both are bad: an id that is
        # not in the list is a client-side state mismatch regardless of what
        # text was submitted. Nothing asserts the opposite precedence -- the
        # blank-text check is exercised at PracticeLogService's own tier.
        flag = self._flag_service.get_flag(flag_id)

        attempt = PracticeAttempt(flag_id=flag.id, attempt_text=attempt_text, timestamp=self._clock())
        self._practice_log_service.record_attempt(attempt)
        logger.info("recorded practice attempt for flag_id=%s", flag.id)
        return attempt
