"""Orchestration service suggesting the next session's scenario.

Composes four service dependencies -- LearnerProfileProcessingService
(Processing) plus IMistakePatternService, ITopicCoveredService, and
IFlagService (all Foundation) -- into a single read-only decision: what
proficiency level, grammar-category focus, and topic Voice Conversation
should open the next Conversation Mode session with.

Composition, not reimplementation: get-or-create profile logic lives in
LearnerProfileProcessingService, find-by-category/find-by-topic logic lives
in MistakePatternProcessingService/TopicCoveredProcessingService -- but
those two Processing services only expose their upsert methods
(record_occurrence/resolve, record_topic), not a list. Reading the full
per-profile list to pick a focus is genuinely this feature's own decision,
so it depends on IMistakePatternService/ITopicCoveredService (Foundation)
directly for their list_*_by_profile() reads, one level below where
MistakePatternProcessingService/TopicCoveredProcessingService themselves
sit. Same shape ReviewOrchestrationService already established -- mixing a
Processing dependency (there: none directly, but the rag orchestration
dependency plays the analogous higher-level role) with Foundation
dependencies (FlagService, PracticeLogService) rather than staying within
one tier, because the tier that has the method this feature needs is what
determines the dependency, not a rule that every dependency must be the
same tier.

Per CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers, ORC-001 (Florance
dep-count limit) is waived for the Orchestration-layer feature set,
extended here to LearnerProfile's session-scenario feature: it coordinates
four dependencies, not two or three. ORC-002 (no direct broker deps) is
NOT waived and holds -- only logging_broker/configuration_broker are held
directly (both cross-cutting, per CLAUDE.md's mapping table), verified at
learner_profile_orchestration_service.py:60-77 below: every other
dependency is a Foundation or Processing service interface, never a broker.

Concrete class declared directly in this file, inheriting the Exceptions
mixin and the LearnerProfileScenarioService Protocol by name -- no separate
"_Base" intermediate class, no composition step in __init__.py, matching
ReviewOrchestrationService's already-rebuilt shape (the old `_ServiceBase`
pattern CLAUDE.md disallows).

Public methods are the ONLY thing that wraps with `_try_catch` (defined in
the Exceptions mixin): the one public method's entire body is an inline
nested closure passed straight to `_try_catch`, not a separate `_do_thing`
private method with its own local try/except -- same convention as Review.
"""

from typing import Callable, List, Optional

from api.brokers.configuration import ConfigurationBroker, EnvConfigurationBroker
from api.brokers.logging import LoggingBroker
from api.models.foundations.mistake_pattern.mistake_pattern import MistakePattern
from api.models.foundations.topic_covered.topic_covered import TopicCovered
from api.models.orchestrations.learner_profile.session_scenario import SessionScenario
from api.services.foundations.flag import IFlagService
from api.services.foundations.mistake_pattern import IMistakePatternService
from api.services.foundations.topic_covered import ITopicCoveredService
from api.services.orchestrations.learner_profile.i_learner_profile_orchestration_service import (
    LearnerProfileScenarioService,
)
from api.services.orchestrations.learner_profile.learner_profile_orchestration_service_exceptions import (
    LearnerProfileOrchestrationServiceExceptions,
)
from api.services.processings.learner_profile import ILearnerProfileProcessingService


class LearnerProfileOrchestrationService(LearnerProfileOrchestrationServiceExceptions, LearnerProfileScenarioService):
    """Owns the next-session-scenario decision across learner memory."""

    def __init__(
        self,
        learner_profile_processing_service: ILearnerProfileProcessingService,
        mistake_pattern_service: IMistakePatternService,
        topic_covered_service: ITopicCoveredService,
        flag_service: IFlagService,
        *,
        logging_broker: LoggingBroker,
        configuration_broker: ConfigurationBroker = EnvConfigurationBroker(),
    ) -> None:
        # ORC-002 check: every dependency above is a Foundation or Processing
        # service interface (I*Service Protocol). Nothing here is imported
        # from api.brokers.* except the two cross-cutting ones immediately
        # below, matching CLAUDE.md's waiver table exactly -- no direct
        # business-broker dependency.
        self._learner_profile_processing_service = learner_profile_processing_service
        self._mistake_pattern_service = mistake_pattern_service
        self._topic_covered_service = topic_covered_service
        self._flag_service = flag_service
        self._logging_broker = logging_broker
        self._configuration_broker = configuration_broker

    def suggest_session_scenario(self) -> SessionScenario:
        def action() -> SessionScenario:
            default_level = self._configuration_broker.get("DEFAULT_PROFICIENCY_LEVEL", "beginner")
            profile = self._learner_profile_processing_service.ensure_profile(default_level)

            patterns = self._mistake_pattern_service.list_mistake_patterns_by_profile(profile.id)
            focus_category = self._pick_focus_category(patterns)

            topics = self._topic_covered_service.list_topic_covered_by_profile(profile.id)
            suggested_topic = focus_category or self._pick_due_topic(topics)

            flag_limit = int(self._configuration_broker.get("RECENT_FLAG_LIMIT", "5"))
            recent_flags = sorted(self._flag_service.list_flags(), key=lambda f: f.timestamp, reverse=True)
            recent_mistake_categories = list(dict.fromkeys(f.category for f in recent_flags[:flag_limit]))

            self._logging_broker.log_info(
                "suggested session scenario: level=%s focus=%r topic=%r",
                profile.proficiency_level,
                focus_category,
                suggested_topic,
            )
            return SessionScenario(
                proficiency_level=profile.proficiency_level or default_level,
                focus_category=focus_category,
                suggested_topic=suggested_topic,
                recent_mistake_categories=recent_mistake_categories,
            )

        return self._try_catch(action)

    @staticmethod
    def _pick_focus_category(patterns: List[MistakePattern]) -> Optional[str]:
        """The active pattern with the most occurrences, or None.

        "Active" only -- a resolved pattern isn't a current focus, even if
        it once had a high occurrence_count.
        """
        active = [p for p in patterns if p.status == "active"]
        return max(active, key=lambda p: p.occurrence_count).category if active else None

    @staticmethod
    def _pick_due_topic(topics: List[TopicCovered]) -> Optional[str]:
        """The topic least recently practiced, or None if nothing is covered
        yet. Only consulted when there's no focus_category to fall back on."""
        return min(topics, key=lambda t: t.last_practiced_at).topic if topics else None


if __name__ == "__main__":
    # ponytail: assert-based self-check for the two pure decision helpers --
    # no framework, confirms the branch logic (active-only filter, max by
    # occurrence_count, min by last_practiced_at, empty-list -> None) a
    # broken edit here would silently flip. Full dependency-wiring behavior
    # (suggest_session_scenario, _try_catch) is covered by the generated
    # unit test suite instead.
    from datetime import datetime

    svc = LearnerProfileOrchestrationService
    assert svc._pick_focus_category([]) is None
    resolved_only = [MistakePattern(id=1, profile_id=1, category="ser_estar", occurrence_count=9, last_seen_at=datetime.now(), status="resolved")]
    assert svc._pick_focus_category(resolved_only) is None
    mixed = [
        MistakePattern(id=1, profile_id=1, category="gender", occurrence_count=2, last_seen_at=datetime.now(), status="active"),
        MistakePattern(id=2, profile_id=1, category="ser_estar", occurrence_count=5, last_seen_at=datetime.now(), status="active"),
    ]
    assert svc._pick_focus_category(mixed) == "ser_estar"

    assert svc._pick_due_topic([]) is None
    topics = [
        TopicCovered(id=1, profile_id=1, topic="past_tense", first_covered_at=datetime(2026, 1, 1), last_practiced_at=datetime(2026, 9, 1)),
        TopicCovered(id=2, profile_id=1, topic="subjunctive", first_covered_at=datetime(2026, 1, 1), last_practiced_at=datetime(2026, 1, 2)),
    ]
    assert svc._pick_due_topic(topics) == "subjunctive"
    print("OK")
