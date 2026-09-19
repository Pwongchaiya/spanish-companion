"""Orchestration service for Progress (roadmap Phase 2: A5 cumulative
mistake dashboard, F1 corpus coverage map, C1 speaking-hours meter, C3
longest unflagged stretch).

Composes four service dependencies -- LearnerProfileProcessingService
(Processing) plus IMistakePatternService, ITopicCoveredService and
ISessionLogEntryService (Foundation) -- into four independent read-only
reports.

A5/F1 needed no new brokers. C1/C3 did, and that is exactly why they were
parked when the rest of Phase 2 shipped: neither per-session duration nor
cross-session flag history existed in any queryable store
(wiki/decisions/progress-dashboard-scope-c1-c3-parked.md). The
`session_log` table added for them is the whole of that new storage; both
reads here are plain folds over its rows.

Neither C1 nor C3 resolves a profile: `session_log` has no profile_id (this
app is single-user by design, see the 0003 migration), so the
ensure_profile() step the A5/F1 reads open with would be a pointless write
on the read path.

Per CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers, ORC-001 (Florance
dep-count limit) is waived for the Orchestration-layer feature set,
extended here the same way LearnerProfileOrchestrationService's
four-dependency case was -- now four dependencies here too, with
ISessionLogEntryService. ORC-002 (no direct broker deps) is NOT waived and
holds -- only logging_broker/configuration_broker are held directly (both
cross-cutting), every other dependency is a Foundation or Processing
service interface, never a broker.

Concrete class declared directly in this file, inheriting the Exceptions
mixin and the ProgressService Protocol by name -- no separate "_Base"
intermediate class, matching every other rebuilt Orchestration service in
this codebase (no `_ServiceBase` composition, per CLAUDE.md).

Public methods are the ONLY thing that wraps with `_try_catch`: each
method's entire body is an inline nested closure passed straight to
`_try_catch`, same convention as Review and LearnerProfile.
"""

from typing import List, Optional

from api.brokers.configuration import ConfigurationBroker, EnvConfigurationBroker
from api.brokers.logging import LoggingBroker
from api.models.foundations.mistake_pattern.mistake_pattern import MistakePattern
from api.models.foundations.session_log_entry.session_log_entry import SessionLogEntry
from api.models.orchestrations.progress.speaking_total import SpeakingTotal
from api.models.orchestrations.progress.topic_coverage_entry import TopicCoverageEntry
from api.models.orchestrations.progress.unflagged_streak import UnflaggedStreak
from api.services.foundations.mistake_pattern import IMistakePatternService
from api.services.foundations.session_log_entry import ISessionLogEntryService
from api.services.foundations.topic_covered import ITopicCoveredService
from api.services.orchestrations.progress.i_progress_service import ProgressService
from api.services.orchestrations.progress.progress_service_exceptions import ProgressOrchestrationServiceExceptions
from api.services.processings.learner_profile import ILearnerProfileProcessingService
from rag.data.topics import TOPICS


class ProgressOrchestrationService(ProgressOrchestrationServiceExceptions, ProgressService):
    """Owns the two read-only progress reports over existing learner data."""

    def __init__(
        self,
        learner_profile_processing_service: ILearnerProfileProcessingService,
        mistake_pattern_service: IMistakePatternService,
        topic_covered_service: ITopicCoveredService,
        session_log_entry_service: ISessionLogEntryService,
        *,
        logging_broker: LoggingBroker,
        configuration_broker: ConfigurationBroker = EnvConfigurationBroker(),
    ) -> None:
        # ORC-002 check: every dependency above is a Foundation or Processing
        # service interface (I*Service Protocol). Nothing here is imported
        # from api.brokers.* except the two cross-cutting ones immediately
        # below.
        self._learner_profile_processing_service = learner_profile_processing_service
        self._mistake_pattern_service = mistake_pattern_service
        self._topic_covered_service = topic_covered_service
        self._session_log_entry_service = session_log_entry_service
        self._logging_broker = logging_broker
        self._configuration_broker = configuration_broker

    def list_mistake_summary(self) -> List[MistakePattern]:
        def action() -> List[MistakePattern]:
            default_level = self._configuration_broker.get("DEFAULT_PROFICIENCY_LEVEL", "beginner")
            profile = self._learner_profile_processing_service.ensure_profile(default_level)
            patterns = self._mistake_pattern_service.list_mistake_patterns_by_profile(profile.id)
            self._logging_broker.log_info("listed %d mistake pattern(s) for progress dashboard", len(patterns))
            return patterns

        return self._try_catch(action)

    def list_topic_coverage(self) -> List[TopicCoverageEntry]:
        def action() -> List[TopicCoverageEntry]:
            default_level = self._configuration_broker.get("DEFAULT_PROFICIENCY_LEVEL", "beginner")
            profile = self._learner_profile_processing_service.ensure_profile(default_level)
            covered = self._topic_covered_service.list_topic_covered_by_profile(profile.id)
            covered_by_topic = {c.topic: c for c in covered}

            distinct_topics = list(dict.fromkeys(topic for topic, _url in TOPICS))
            entries = [
                TopicCoverageEntry(
                    topic=topic,
                    covered=topic in covered_by_topic,
                    first_covered_at=covered_by_topic[topic].first_covered_at if topic in covered_by_topic else None,
                )
                for topic in distinct_topics
            ]
            self._logging_broker.log_info(
                "built corpus coverage map: %d/%d topics covered",
                sum(1 for e in entries if e.covered),
                len(entries),
            )
            return entries

        return self._try_catch(action)

    def get_speaking_total(self) -> SpeakingTotal:
        def action() -> SpeakingTotal:
            completed = _completed_sessions(self._session_log_entry_service.list_session_log_entries())
            total_seconds = sum((entry.ended_at - entry.started_at).total_seconds() for entry in completed)
            self._logging_broker.log_info(
                "computed speaking total: %.1fs across %d completed session(s)", total_seconds, len(completed)
            )
            return SpeakingTotal(total_seconds=total_seconds, session_count=len(completed))

        return self._try_catch(action)

    def get_longest_unflagged_streak(self) -> UnflaggedStreak:
        def action() -> UnflaggedStreak:
            completed = _completed_sessions(self._session_log_entry_service.list_session_log_entries())
            longest = current = 0
            for entry in completed:
                current = current + 1 if entry.flag_count == 0 else 0
                longest = max(longest, current)
            self._logging_broker.log_info("computed unflagged streak: longest %d, current %d", longest, current)
            return UnflaggedStreak(longest=longest, current=current)

        return self._try_catch(action)

    def get_latest_completed_session(self) -> Optional[SessionLogEntry]:
        def action() -> Optional[SessionLogEntry]:
            completed = _completed_sessions(self._session_log_entry_service.list_session_log_entries())
            latest = completed[-1] if completed else None
            self._logging_broker.log_info(
                "resolved latest completed session for recap: %s", latest.id if latest else None
            )
            return latest

        return self._try_catch(action)


def _completed_sessions(entries: List[SessionLogEntry]) -> List[SessionLogEntry]:
    """The `session_log` rows both C1 and C3 are allowed to count.

    A row with no `ended_at` is either still running or belongs to a
    process that was killed before it could finish writing (see
    ConversationOrchestrationService._end_session_log_entry). Skipping it is
    not just about duration: its `flag_count` is still the insert-time 0,
    which C3 would otherwise read as a genuine zero-flag session and use to
    extend a streak that never happened.

    Rows whose `ended_at` precedes `started_at` are dropped too -- a clock
    change mid-session is the only way to produce one, and a negative
    duration would silently eat real hours out of the C1 total.

    Ordering is preserved (the broker already sorts by `started_at`), which
    is what makes C3's single pass meaningful.
    """
    return [e for e in entries if e.ended_at is not None and e.ended_at >= e.started_at]


if __name__ == "__main__":
    # ponytail: assert-based self-check for the pure topic-coverage merge
    # logic (dedupe + covered/not-covered split) -- no framework, mirrors
    # LearnerProfileOrchestrationService's own __main__ self-check for its
    # pure decision helpers. Full dependency-wiring behavior (_try_catch,
    # ensure_profile composition) is covered by the generated unit test
    # suite instead.
    # Uses the real rag/data/topics.py TOPICS -- "preterite-vs-imperfect"
    # genuinely appears twice there (two URLs, one topic), which is exactly
    # the dedupe case worth checking. Not monkeypatched: patching this
    # module's TOPICS global only works when tests import it as
    # api.services.orchestrations.progress.progress_service, but running
    # this file directly (`python -m ...`) re-executes it as a second,
    # separate __main__ module object with its own TOPICS binding -- the
    # patch would silently miss it.
    from datetime import datetime

    from unittest.mock import Mock

    assert len([t for t, _ in TOPICS if t == "preterite-vs-imperfect"]) > 1, "fixture assumption changed"

    svc = ProgressOrchestrationService(
        learner_profile_processing_service=Mock(ensure_profile=Mock(return_value=Mock(id=1))),
        mistake_pattern_service=Mock(),
        topic_covered_service=Mock(
            list_topic_covered_by_profile=Mock(
                return_value=[Mock(topic="ser-vs-estar", first_covered_at=datetime(2026, 1, 1))]
            )
        ),
        session_log_entry_service=Mock(),
        logging_broker=Mock(),
    )
    entries = svc.list_topic_coverage()
    distinct_topics = [topic for topic, _url in TOPICS]
    assert [e.topic for e in entries] == list(dict.fromkeys(distinct_topics)), entries
    assert sum(1 for e in entries if e.topic == "preterite-vs-imperfect") == 1, "duplicate topic not deduped"
    ser_estar_entry = next(e for e in entries if e.topic == "ser-vs-estar")
    assert ser_estar_entry.covered is True and ser_estar_entry.first_covered_at == datetime(2026, 1, 1)
    other_entry = next(e for e in entries if e.topic != "ser-vs-estar")
    assert other_entry.covered is False and other_entry.first_covered_at is None
    print("progress_service self-check passed")
