"""Orchestration service for Review Mode.

Composes four dependencies -- two brokers (FlagBroker, PracticeLogBroker) and
two in-process rag controllers (RetrievalController, GenerationController) --
into the Review Mode flow: flagged list -> selection -> grounded explanation ->
single practice attempt.

Composition, not reimplementation: retrieval ranking lives in
rag/services/retrieval/, prompt-building and LLM-failure fallback live in
rag/services/generation.py. What is genuinely Review's own is here and only
here: looking a flag up by id, and deciding what happens when the corpus has
no match.

Importing rag.controllers.* from api is the one deliberate package-boundary
crossing (api -> rag, never the reverse) -- these are rag's public entry
points, so this is the sanctioned call, not a layering violation.

Per CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers, ORC-001 (Florance
dep-count limit) and ORC-002 (no direct broker deps) are waived: there is no
Foundation layer beneath this service, so depending on brokers directly is
correct here.
"""

import logging
import os
from datetime import datetime
from typing import Callable

from dotenv import load_dotenv

from api.brokers.flag import FlagBroker
from api.brokers.practice_log import PracticeAttempt, PracticeLogBroker
from api.errors import ApiError
from api.models.flag import Flag
from rag.controllers.generation import GenerationController
from rag.controllers.retrieval import RetrievalController
from rag.models.generation import Explanation

load_dotenv()

logger = logging.getLogger(__name__)

# ponytail: one knob -> plain os.getenv at import time, same pattern as
# api/services/session_lifecycle.py and rag/db.py (load_dotenv() then
# os.getenv with a string default, cast at the read site).
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "3"))


class FlagNotFoundException(ApiError):
    """Raised when no flag in the current list has the requested id.

    The only exception this feature names. Deliberately not a hierarchy --
    the 9-class default is waived per CLAUDE.md, and every other failure here
    already has an owner: retrieval returning nothing is handled (not raised),
    LLM failure is Generation's fallback, and a missing/corrupt flags file is
    FlagBroker.load_flags()'s documented [] .
    """

    def __init__(self, flag_id: str) -> None:
        super().__init__(f"No flag found with id {flag_id!r}")


class ReviewOrchestrator:
    """Owns Review Mode's flow across flags, retrieval, generation, practice."""

    def __init__(
        self,
        flag_broker: FlagBroker,
        practice_log_broker: PracticeLogBroker,
        retrieval_controller: RetrievalController,
        generation_controller: GenerationController,
        clock: Callable[[], datetime] = datetime.now,
    ) -> None:
        self._flag_broker = flag_broker
        self._practice_log_broker = practice_log_broker
        self._retrieval = retrieval_controller
        self._generation = generation_controller
        # Injected for the same reason session_lifecycle.py injects
        # time_source: CLAUDE.md's unit-test rule forbids live datetime.now().
        self._clock = clock

    def list_flags(self) -> list[Flag]:
        """The current flag list, for the UI's flagged-list -> selection step.

        Pass-through: FlagBroker.load_flags() already returns [] for a missing
        or corrupt file, and "no flags yet" is a normal state, not an error.
        """
        return self._flag_broker.load_flags()

    def explain_flag(self, flag_id: str) -> Explanation:
        """Grounded explanation of one flag, chosen by id.

        Raises:
            FlagNotFoundException: no flag in the current list has this id.
        """
        flag = self._get_flag(flag_id)

        chunks = self._retrieval.retrieve(
            query=flag.corrected,
            top_k=RETRIEVAL_TOP_K,
            category=flag.category,
        )
        if not chunks:
            # Review's problem, not Generation's: GenerationController.explain()
            # requires a real chunk (its contract has no Optional), so calling it
            # here would be a contract violation, not a graceful degradation.
            #
            # This log line is the ONLY thing distinguishing this failure mode
            # (corpus has nothing on the topic -> ingest more RAE pages) from
            # Generation's LLM failure (rag/services/generation.py:38 -> retry),
            # because both deliberately return the same user-facing string.
            logger.info("no corpus match for flag_id=%s category=%r", flag_id, flag.category)
            # Phase 1's exact fallback string, review/review.py:107 — preserve
            # verbatim, same as GenerationService's. One user-facing "couldn't
            # help with this" string across the system; debugging splits them in
            # the logs above, not in the copy.
            return Explanation(explanation="I'm not certain on that one.", source_url="")

        # retrieve() returns best-first, so [0] is the top-ranked chunk.
        return self._generation.explain(flag, chunks[0])

    def record_practice(self, flag_id: str, attempt_text: str) -> PracticeAttempt:
        """Log the learner's single practice attempt at a flag's correction.

        Returns the recorded attempt so the caller has its timestamp without
        reconstructing one from a second clock read.

        Raises:
            FlagNotFoundException: no flag in the current list has this id.
        """
        # Look the flag up purely to reject unknown ids -- same not-found
        # handling as explain_flag. A practice attempt against a flag that
        # isn't in the list is a client-side state mismatch worth surfacing,
        # not an orphan row worth writing.
        flag = self._get_flag(flag_id)

        attempt = PracticeAttempt(flag_id=flag.id, attempt_text=attempt_text, timestamp=self._clock())
        self._practice_log_broker.record_attempt(attempt)
        logger.info("recorded practice attempt for flag_id=%s", flag.id)
        return attempt

    def _get_flag(self, flag_id: str) -> Flag:
        # ponytail: linear scan of a freshly loaded list on every call. MVP
        # scale is one conversation's flags (tens), and reloading each time is
        # the point -- Voice Conversation rewrites the file mid-session, so a
        # cached dict would go stale. Build an id->Flag index only if a single
        # request ever needs more than one lookup.
        for flag in self._flag_broker.load_flags():
            if flag.id == flag_id:
                return flag
        raise FlagNotFoundException(flag_id)
