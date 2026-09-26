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

Concrete class declared directly in this file, inheriting the Exceptions
mixin (review_service_exceptions.py) and the ReviewService Protocol
(i_review_service.py) by name -- no separate "_Base" intermediate class, no
composition step in __init__.py. Matches LearnerProfileService's rebuilt
shape (the previous `_ReviewOrchestrationServiceBase` + __init__.py
composition step was the invented-`_ServiceBase` pattern CLAUDE.md
explicitly disallows -- removed). No Validations mixin: the one check that
lived here (blank attempt_text) belongs to PracticeLogService, so nothing is
validated at this tier.

Public methods are the ONLY thing that wraps with `_try_catch` (defined in
the Exceptions mixin): each public method's entire body is an inline nested
closure passed straight to `_try_catch`, not a separate `_do_thing` private
method with its own local try/except. No local try/except inside the
closures: every exception -- domain leaf, dependency wrapper, or otherwise --
propagates untouched to `_try_catch`, the single dispatch point that
classifies and wraps.
"""

from dataclasses import replace
from datetime import datetime
from functools import lru_cache
from typing import Callable, List, Optional

from api.brokers.configuration import ConfigurationBroker, EnvConfigurationBroker
from api.data.roleplay_scenarios import get_roleplay_scenario
from api.brokers.logging import LoggingBroker
from api.brokers.practice_log import PracticeAttempt
from api.models.foundations.flag import Flag
from api.models.foundations.mistake_pattern.exceptions import NotFoundMistakePatternException
from api.models.orchestrations.review.dictation import DictationExercise, DictationResult
from api.models.orchestrations.review.practice_result import PracticeResult
from api.models.orchestrations.review.task_outcome import TaskOutcome
from api.services.foundations.flag import IFlagService
from api.services.foundations.live_transcript import ILiveTranscriptService
from api.services.foundations.practice_log import IPracticeLogService
from api.services.foundations.session_log_entry import ISessionLogEntryService
from api.services.orchestrations.review._dictation import check_dictation
from api.services.orchestrations.review.i_review_service import ReviewService
from api.services.orchestrations.review.review_service_exceptions import ReviewOrchestrationServiceExceptions
from api.services.processings.ingestion_queue import IIngestionQueueProcessingService
from api.services.processings.learner_profile import ILearnerProfileProcessingService
from api.services.processings.mistake_pattern import IMistakePatternProcessingService
from api.services.processings.topic_covered import ITopicCoveredProcessingService
from rag.data.topics import TOPICS
from rag.models.foundations.generation import FALLBACK_EXPLANATION, Explanation
from rag.services.foundations.generation import GenerationService
from rag.services.orchestrations.retrieval import HybridRetrievalOrchestrationService
from rag.services.orchestrations.retrieval.strategies.filters import category_matches_topic

# F1 follow-up: distinct corpus topics, first-appearance order -- same
# dict.fromkeys dedupe ProgressOrchestrationService.list_topic_coverage()
# already uses over this same TOPICS list.
_CORPUS_TOPICS = list(dict.fromkeys(topic for topic, _url in TOPICS))


class ReviewOrchestrationService(ReviewOrchestrationServiceExceptions, ReviewService):
    """Owns Review Mode's flow across flags, retrieval, generation, practice."""

    def __init__(
        self,
        flag_service: IFlagService,
        practice_log_service: IPracticeLogService,
        retrieval_service: HybridRetrievalOrchestrationService,
        generation_service: GenerationService,
        learner_profile_processing_service: ILearnerProfileProcessingService,
        mistake_pattern_processing_service: IMistakePatternProcessingService,
        session_log_entry_service: ISessionLogEntryService,
        live_transcript_service: ILiveTranscriptService,
        ingestion_queue_processing_service: IIngestionQueueProcessingService,
        topic_covered_processing_service: ITopicCoveredProcessingService,
        clock: Callable[[], datetime] = datetime.now,
        *,
        logging_broker: LoggingBroker,
        configuration_broker: ConfigurationBroker = EnvConfigurationBroker(),
    ) -> None:
        self._flag_service = flag_service
        self._practice_log_service = practice_log_service
        self._retrieval_service = retrieval_service
        self._generation_service = generation_service
        # LearnerProfile Phase 2: record_practice() judges the attempt and
        # writes the verdict to mistake_pattern -- both new dependencies are
        # Processing-tier, same convention LearnerProfileOrchestrationService
        # already established (ORC-001 dep-count waiver already covers Review).
        self._learner_profile_processing_service = learner_profile_processing_service
        self._mistake_pattern_processing_service = mistake_pattern_processing_service
        # D4: get_task_outcome() reads the latest session_log row + its
        # transcript and writes the judged outcome back.
        self._session_log_entry_service = session_log_entry_service
        self._live_transcript_service = live_transcript_service
        # F2: explain_flag() records a still-weak grounding verdict against
        # the retrieved topic (Processing-tier, ORC-001 waiver covers the count).
        self._ingestion_queue_processing_service = ingestion_queue_processing_service
        # F1 follow-up: corpus-coverage map was always 0/7 because nothing
        # called record_topic() in production -- explain_flag() and
        # record_practice() below are the two producers.
        self._topic_covered_processing_service = topic_covered_processing_service
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

    def set_flag_status(self, flag_id: str, status: str) -> Flag:
        def action() -> Flag:
            # get_flag() raises FlagValidationException (wrapping
            # NotFoundFlagException) for an unknown id -- same not-found
            # check every other flag_id-taking method here already uses
            # (explain_flag, record_practice, check_dictation).
            flag = self._flag_service.get_flag(flag_id)
            updated_flag = replace(flag, status=status)
            flags = self._flag_service.list_flags()
            new_flags = [updated_flag if f.id == flag_id else f for f in flags]
            # save_flags() raises FlagValidationException (wrapping
            # InvalidFlagStatusException) for a status outside FLAG_STATUSES
            # -- the Exposer already rejects that with a 400 before ever
            # reaching here, this is defense-in-depth for any other caller,
            # same shape as record_practice's attempt_text double-check.
            self._flag_service.save_flags(new_flags)
            return updated_flag

        return self._try_catch(action)

    # ponytail: flags are immutable once created and the corpus is a static
    # seeded set, so a given flag_id's explanation never changes -- cache
    # forever instead of re-running retrieval + an LLM call on every repeat
    # view. lru_cache only caches successful returns, so a _try_catch-raised
    # exception is never cached. Caches on (self, flag_id); safe because
    # exactly one ReviewOrchestrationService is constructed per process.
    @lru_cache(maxsize=None)
    def explain_flag(self, flag_id: str) -> Explanation:
        def action() -> Explanation:
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
                # One user-facing "couldn't help with this" string across the
                # system (FALLBACK_EXPLANATION, rag/models/foundations/generation);
                # debugging splits them in the logs above, not in the copy.
                return Explanation(explanation=FALLBACK_EXPLANATION, source_url="", source_excerpt="")

            # #64: pass the full retrieved (best-first) chunk list --
            # GenerationService itself decides how many of them (EXPLAIN_TOP_K)
            # actually ground the explanation. Topic bookkeeping below still
            # uses chunks[0]'s topic -- per CLAUDE.md's Phase-2 waiver, weak-
            # verdict/topic recording may keep using the top chunk's topic.
            explanation = self._generation_service.explain(flag, chunks)
            if explanation.is_fallback:
                explanation = self._second_opinion(flag, retrieval_top_k) or explanation
            if explanation.is_fallback:
                self._record_weak_verdict(flag.id, chunks[0].topic)
            else:
                self._record_topic_for_explanation(flag.id, chunks[0].topic)
            return explanation

        return self._try_catch(action)

    def _record_topic_for_explanation(self, flag_id: str, topic: str) -> None:
        """F1 follow-up: a grounded (non-fallback) explanation means the
        corpus actually covered this topic -- record it so Progress's
        coverage map reflects it. Uses the top chunk's topic, same source
        _record_weak_verdict uses for the opposite (weak) outcome.

        Best-effort like _record_weak_verdict: a profile-lookup or write
        failure here must never change the explanation already produced.
        """
        try:
            default_level = self._configuration_broker.get("DEFAULT_PROFICIENCY_LEVEL", "beginner")
            profile = self._learner_profile_processing_service.ensure_profile(default_level)
            self._topic_covered_processing_service.record_topic(profile.id, topic)
        except Exception as e:  # ponytail: best-effort -- coverage bookkeeping must never break Review
            self._logging_broker.log_info("topic_covered record failed for flag_id=%s topic=%s: %s", flag_id, topic, e)

    def _record_weak_verdict(self, flag_id: str, topic: str) -> None:
        """F2: count a still-weak grounded explanation against the top chunk's
        RAE topic (a `TOPICS` key -- chunk.topic is written from it at ingest),
        so the ingestion queue can grow the corpus where it keeps failing.

        Best-effort: any failure is logged and swallowed, never changing the
        explanation Review returns.
        """
        try:
            self._ingestion_queue_processing_service.record_weak_verdict(topic, self._clock())
        except Exception as e:  # ponytail: best-effort -- queue bookkeeping must never break Review
            self._logging_broker.log_info(
                "ingestion queue record failed for flag_id=%s topic=%s: %s", flag_id, topic, e
            )

    def _second_opinion(self, flag: Flag, top_k: int) -> Optional[Explanation]:
        """F4: one lexical re-retrieve + regenerate after a weak grounding verdict.

        Returns the new explanation only if it passed grounding; None (caller
        keeps the original fallback) when disabled, nothing found, still weak,
        or the pass itself failed. Capped at one attempt.
        """
        if self._configuration_broker.get("SECOND_OPINION_ENABLED", "false").lower() != "true":
            return None
        try:
            chunks = self._retrieval_service.retrieve(
                query=flag.corrected, top_k=top_k, category=flag.category, alternate=True
            )
            if not chunks:
                self._logging_broker.log_info("second opinion found no chunks for flag_id=%s", flag.id)
                return None
            # #64: same top-k grounding as the primary attempt above.
            second = self._generation_service.explain(flag, chunks)
        except Exception as e:  # ponytail: best-effort -- any failure degrades to the original explanation
            self._logging_broker.log_info("second opinion failed for flag_id=%s: %s", flag.id, e)
            return None
        if second.is_fallback:
            self._logging_broker.log_info("second opinion still weak for flag_id=%s", flag.id)
            return None
        self._logging_broker.log_info("second opinion recovered flag_id=%s", flag.id)
        return second

    def get_task_outcome(self) -> Optional[TaskOutcome]:
        def action() -> Optional[TaskOutcome]:
            # Latest *completed* session: an in-flight row has no finished
            # transcript to judge (same skip rule as the Progress aggregates).
            completed = [e for e in self._session_log_entry_service.list_session_log_entries() if e.ended_at]
            if not completed:
                return None
            entry = completed[-1]
            scenario = get_roleplay_scenario(entry.scenario_slug) if entry.scenario_slug else None
            if scenario is None or not scenario.success_condition:
                return None

            outcome = entry.task_outcome
            if outcome is None:
                # Judged here, in Review Mode, on first view -- never live.
                transcript_text = self._live_transcript_service.read_full_text()
                if transcript_text:
                    outcome = self._generation_service.judge_task_outcome(transcript_text, scenario.success_condition)
                    if outcome is not None:
                        self._session_log_entry_service.set_task_outcome(entry.id, outcome)
                        self._logging_broker.log_info(
                            "judged task outcome for session_log id=%s scenario=%s: %s",
                            entry.id,
                            scenario.slug,
                            outcome,
                        )
            return TaskOutcome(
                scenario_slug=scenario.slug,
                label=scenario.label,
                success_condition=scenario.success_condition,
                outcome=outcome,
            )

        return self._try_catch(action)

    def record_practice(self, flag_id: str, attempt_text: str, roleplay_slug: Optional[str] = None) -> PracticeResult:
        def action() -> PracticeResult:
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

            # LearnerProfile Phase 4: a known slug resolves to its setting text
            # here, api-side, before crossing into rag -- rag must never import
            # api/data (one-directional dependency). An unrecognized slug (the
            # Exposer already rejects one with a 400 -- see api/exposers/
            # review.py -- so this is only reachable from another caller) is
            # silently treated as no roleplay context, same "optional, never
            # load-bearing" shape as the scenario picker elsewhere.
            roleplay = get_roleplay_scenario(roleplay_slug) if roleplay_slug else None
            # A2 (graded practice-attempt verdict): judged BEFORE the attempt
            # is persisted (moved up from after -- see decision note below),
            # so `grade` can be written into the durable PracticeAttempt
            # record itself rather than a separate, un-attachable field --
            # the JSONL log is append-only, there is no update path.
            # `mastered: bool` is derived here, not inside GenerationService,
            # so every existing mastered-based consumer is unaffected.
            grade = self._generation_service.judge_practice_attempt(
                flag, attempt_text, roleplay.setting if roleplay else None
            )
            mastered = grade in ("good", "easy")

            attempt = PracticeAttempt(flag_id=flag.id, attempt_text=attempt_text, timestamp=self._clock(), grade=grade)
            self._practice_log_service.record_attempt(attempt)
            self._logging_broker.log_info("recorded practice attempt for flag_id=%s, grade=%s", flag.id, grade)

            # LearnerProfile Phase 2: write the verdict to mistake_pattern.
            # Single-user app -- default_level matches
            # LearnerProfileOrchestrationService's own config key, so a
            # profile created here or there converges on the same default.
            default_level = self._configuration_broker.get("DEFAULT_PROFICIENCY_LEVEL", "beginner")
            profile = self._learner_profile_processing_service.ensure_profile(default_level)
            if mastered:
                # F1 follow-up: a mastered attempt means the learner correctly
                # used this category -- map it to a corpus topic (first match
                # wins; no match means nothing worth recording) the same way
                # CategoryBoostFilter grounds a flag's category at retrieval time.
                matched_topic = next(
                    (topic for topic in _CORPUS_TOPICS if category_matches_topic(topic, flag.category)), None
                )
                if matched_topic is not None:
                    self._record_topic_for_practice(flag.id, profile.id, matched_topic)
                try:
                    self._mistake_pattern_processing_service.resolve(profile.id, flag.category)
                except NotFoundMistakePatternException:
                    # Nothing to resolve -- this category never had a recorded
                    # occurrence (e.g. its first-ever practice attempt was
                    # mastered on the first try). Not a failure, Review's own
                    # business decision, same shape as explain_flag's
                    # no-corpus-match fallback.
                    self._logging_broker.log_info(
                        "practice mastered for category=%s but no mistake_pattern existed to resolve",
                        flag.category,
                    )
            else:
                self._mistake_pattern_processing_service.record_occurrence(profile.id, flag.category)

            # A1 (half-life scheduler): advance the review schedule for the
            # judged attempt. Runs after resolve/record_occurrence so a
            # first-ever occurrence exists to schedule; a mastered attempt
            # with no pattern has nothing to schedule -- same not-found
            # handling as the resolve branch above.
            try:
                self._mistake_pattern_processing_service.record_review(profile.id, flag.category, grade)
            except NotFoundMistakePatternException:
                self._logging_broker.log_info("no mistake_pattern to schedule for category=%s", flag.category)

            return PracticeResult(attempt=attempt, mastered=mastered, grade=grade)

        return self._try_catch(action)

    def _record_topic_for_practice(self, flag_id: str, profile_id: int, topic: str) -> None:
        """F1 follow-up: mirrors _record_topic_for_explanation, but the
        profile is already in hand here (record_practice fetches it above
        for the mistake_pattern write), so this only wraps the record_topic
        call itself.
        """
        try:
            self._topic_covered_processing_service.record_topic(profile_id, topic)
        except Exception as e:  # ponytail: best-effort -- coverage bookkeeping must never break Review
            self._logging_broker.log_info("topic_covered record failed for flag_id=%s topic=%s: %s", flag_id, topic, e)

    def get_dictation_exercise(self, exclude_flag_id: Optional[str] = None) -> Optional[DictationExercise]:
        def action() -> Optional[DictationExercise]:
            eligible = [f for f in self._flag_service.list_flags() if f.corrected.strip() and f.id != exclude_flag_id]
            if not eligible:
                return None
            # Deterministic: most-repeated mistake first, newest next, id as
            # the final tiebreak. ponytail: no randomness -- the UI's
            # "another" passes exclude_flag_id; upgrade to a rotating queue
            # if that feels repetitive.
            best = min(eligible, key=lambda f: (-f.occurrence_count, -f.timestamp.timestamp(), f.id))
            return DictationExercise(flag_id=best.id, target=best.corrected)

        return self._try_catch(action)

    def check_dictation(self, flag_id: str, typed_text: str) -> DictationResult:
        def action() -> DictationResult:
            flag = self._flag_service.get_flag(flag_id)
            words = check_dictation(typed_text, flag.corrected)
            return DictationResult(
                flag_id=flag.id,
                target=flag.corrected,
                typed_text=typed_text,
                matches=all(w.status == "ok" for w in words),
                words=words,
            )

        return self._try_catch(action)
