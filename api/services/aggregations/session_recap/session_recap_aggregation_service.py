"""Aggregation service for the post-session recap card (roadmap item C2).

CLAUDE.md's first real trigger for the Aggregation layer: every Exposer in
this codebase up to now calls exactly one Orchestration service (see
api/services/aggregations/README.md, now superseded by this file). This one
needs two -- ProgressOrchestrationService (which session just completed, its
boundary timestamps, its flag_count) and ReviewOrchestrationService (that
session's flagged categories) -- so it earns its own layer above both,
consumed by a single new Exposer route (GET /progress/recap).

No new schema. `session_log` (started_at/ended_at/flag_count) and
flags.json (fully overwritten per session by
FlagService.save_flags(session_flags) at session end -- see
voice_conversation_service.py's run()) already carry everything a recap
needs, with no FK or timestamp-range join required: flags.json's current
contents ARE the most recently completed session's flags, by construction.

Two fields a first-pass wishlist would expect -- "topics touched" and a
practice/mastered count -- are deliberately NOT in SessionRecap. Both would
require inventing a session link that does not exist today:
- topic_covered rows carry no session id, only cumulative
  first_covered_at/last_practiced_at across every session ever, and
  record_topic() (api/services/processings/topic_covered/) has no caller
  anywhere in this codebase yet -- there is nothing to filter by session
  even in principle.
- mistake_pattern rows are likewise cumulative per (profile_id, category),
  and practice attempts happen in Review Mode, strictly AFTER a session
  ends and this recap is first shown -- there is no session boundary a
  practice attempt could be checked against that would mean what "practice
  results from this session" implies.
Composing either honestly needs a new persisted session link, which is a
schema change and therefore needs the user's sign-off per CLAUDE.md's "Ask
Before Building" rule -- out of scope for this dispatch. Reported as a
scoping call, not silently invented.

Concrete class declared directly in this file, inheriting the Exceptions
mixin and the SessionRecapAggregationService Protocol by name -- no separate
"_Base" intermediate class, matching every other rebuilt service in this
codebase (no `_ServiceBase` composition, per CLAUDE.md).

Public methods are the ONLY thing that wraps with `_try_catch` via an inline
nested closure, same convention as every Orchestration service here.
"""

from typing import Optional

from api.brokers.logging import LoggingBroker
from api.models.aggregations.session_recap.session_recap import SessionRecap
from api.services.aggregations.session_recap.i_session_recap_aggregation_service import (
    SessionRecapAggregationService as ISessionRecapAggregationService,
)
from api.services.aggregations.session_recap.session_recap_aggregation_service_exceptions import (
    SessionRecapAggregationServiceExceptions,
)
from api.services.orchestrations.progress.i_progress_service import ProgressService
from api.services.orchestrations.review.i_review_service import ReviewService


class SessionRecapAggregationService(SessionRecapAggregationServiceExceptions, ISessionRecapAggregationService):
    """Owns the one composition Progress/Review don't do on their own:
    pairing a completed session's boundary/flag_count with that same
    session's flagged categories."""

    def __init__(
        self,
        review_service: ReviewService,
        progress_service: ProgressService,
        *,
        logging_broker: LoggingBroker,
    ) -> None:
        # Both dependencies are Orchestration-tier service interfaces --
        # nothing here touches a broker or a Foundation/Processing service
        # directly. That is the whole point of sitting one layer above them.
        self._review_service = review_service
        self._progress_service = progress_service
        self._logging_broker = logging_broker

    def get_latest_recap(self) -> Optional[SessionRecap]:
        def action() -> Optional[SessionRecap]:
            latest_session = self._progress_service.get_latest_completed_session()
            if latest_session is None:
                self._logging_broker.log_info("no completed session yet -- nothing to recap")
                return None

            flags = self._review_service.list_flags()
            categories_flagged = sorted({flag.category for flag in flags})

            self._logging_broker.log_info(
                "built session recap: session_id=%s flag_count=%d categories=%d",
                latest_session.id,
                latest_session.flag_count,
                len(categories_flagged),
            )
            return SessionRecap(
                flag_count=latest_session.flag_count,
                categories_flagged=categories_flagged,
                session_started_at=latest_session.started_at,
                session_ended_at=latest_session.ended_at,
            )

        return self._try_catch(action)


if __name__ == "__main__":
    # ponytail: assert-based self-check for the pure composition logic
    # (category dedupe/sort, None-passthrough for "no session yet") -- no
    # framework, mirrors ProgressOrchestrationService's own __main__
    # self-check. Exception-wrapping behavior is covered by the generated
    # unit test suite instead (tests/unit/services/session_recap/).
    from datetime import datetime
    from unittest.mock import Mock

    svc = SessionRecapAggregationService(
        review_service=Mock(
            list_flags=Mock(
                return_value=[
                    Mock(category="ser-vs-estar"),
                    Mock(category="gender-agreement"),
                    Mock(category="ser-vs-estar"),  # duplicate category, same session
                ]
            )
        ),
        progress_service=Mock(
            get_latest_completed_session=Mock(
                return_value=Mock(
                    id=1,
                    flag_count=3,
                    started_at=datetime(2026, 9, 18, 18, 0, 0),
                    ended_at=datetime(2026, 9, 18, 18, 20, 0),
                )
            )
        ),
        logging_broker=Mock(),
    )
    recap = svc.get_latest_recap()
    assert recap is not None
    assert recap.flag_count == 3
    assert recap.categories_flagged == ["gender-agreement", "ser-vs-estar"], "must dedupe + sort"
    assert recap.session_started_at == datetime(2026, 9, 18, 18, 0, 0)
    assert recap.session_ended_at == datetime(2026, 9, 18, 18, 20, 0)

    svc_no_session = SessionRecapAggregationService(
        review_service=Mock(),
        progress_service=Mock(get_latest_completed_session=Mock(return_value=None)),
        logging_broker=Mock(),
    )
    assert svc_no_session.get_latest_recap() is None, "no completed session -> no recap"
    print("session_recap_aggregation_service self-check passed")
