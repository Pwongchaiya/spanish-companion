"""Orchestration service for Review Mode.

Composes four service dependencies -- two api Foundation services
(FlagService, PracticeLogService) and two rag services (HybridRetrievalOrchestrationService,
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
review_service_exceptions.py), combined into the concrete ReviewOrchestrationService
in __init__.py -- mirrors C#'s `partial class` merging
EntitlementCodesOrchestrationService.cs / .Exeptions.cs into one class, the
same multi-inheritance-merge already used for Session Lifecycle in this
codebase. No Validations mixin: the one check that lived here
(blank attempt_text) now belongs to PracticeLogService, so nothing is
validated at this tier.
"""

from datetime import datetime
from functools import lru_cache
from typing import Callable, List

from api.brokers.configuration import ConfigurationBroker, EnvConfigurationBroker
from api.brokers.logging import LoggingBroker
from api.brokers.practice_log import PracticeAttempt
from api.models.foundations.flag import Flag
from api.services.foundations.flag import IFlagService
from api.services.foundations.practice_log import IPracticeLogService
from rag.models.foundations.generation import Explanation
from rag.services.foundations.generation import GenerationService
from rag.services.orchestrations.retrieval import HybridRetrievalOrchestrationService


class _ReviewOrchestrationServiceBase:
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
        retrieval_service: HybridRetrievalOrchestrationService,
        generation_service: GenerationService,
        clock: Callable[[], datetime] = datetime.now,
        *,
        logging_broker: LoggingBroker,
        configuration_broker: ConfigurationBroker = EnvConfigurationBroker(),
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
        self._configuration_broker = configuration_broker

    def list_flags(self) -> List[Flag]:
        """The current flag list, for the UI's flagged-list -> selection step.

        Routed through _try_catch like every other method here. It used to be
        a bare pass-through, on the argument that FlagBroker.load_flags()
        already returns [] for a missing or corrupt file so "no flags yet" is
        a normal state rather than an error. That argument covered the empty
        case and nothing else: an unreadable flag file, a permission error, or
        any other broker failure escaped this service unwrapped and reached
        Flask raw, which is H7 of the architecture conformance audit. Empty is
        still returned as [], not raised -- only genuine failures now leave as
        wrappers.
        """
        return self._try_catch(self._flag_service.list_flags)

    # ponytail: flags are immutable once created and the corpus is a static
    # seeded set, so a given flag_id's explanation never changes -- cache
    # forever instead of re-running retrieval + an LLM call on every repeat
    # view. lru_cache only caches successful returns, so a _try_catch-raised
    # exception is never cached. Caches on (self, flag_id); safe because
    # exactly one ReviewOrchestrationService is constructed per process.
    @lru_cache(maxsize=None)
    def explain_flag(self, flag_id: str) -> Explanation:
        return self._try_catch(lambda: self._explain_flag(flag_id))

    def _explain_flag(self, flag_id: str) -> Explanation:
        flag = self._flag_service.get_flag(flag_id)

        retrieval_top_k = int(self._configuration_broker.get("RETRIEVAL_TOP_K", "3"))
        chunks = self._retrieval_service.retrieve(
            query=flag.corrected,
            top_k=retrieval_top_k,
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
            self._logging_broker.log_info("no corpus match for flag_id=%s category=%r", flag_id, flag.category)
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
        self._logging_broker.log_info("recorded practice attempt for flag_id=%s", flag.id)
        return attempt
