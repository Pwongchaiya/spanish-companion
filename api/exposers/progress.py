"""Flask Blueprint exposing Progress (roadmap Phase 2: A5/F1/C1/C3) and the
post-session recap (roadmap C2) over HTTP.

Thin mapping layer only -- see api/services/orchestrations/progress/ for the
mistake-summary / topic-coverage / speaking-total / unflagged-streak reads,
and api/services/aggregations/session_recap/ for the recap composition
GET /recap wraps. Routes are unversioned per CLAUDE.md's Phase 2
Layer-Agent Mapping & Waivers (/api/V1.0/ is waived), prefixed /progress.
/recap lives in this same file rather than a new one-route exposer -- same
precedent CLAUDE.md already established for RetrievalController/
GenerationController's deletion.

ProgressOrchestrationService and SessionRecapAggregationService are
constructed from their dependencies by api/app.py and injected here via
make_progress_blueprint(). This module never constructs either, or any of
their dependencies, itself.

Origin/Referer CSRF-shaped checking is NOT implemented here -- it lives
app-wide in api/app.py, applied uniformly across every route.

All five routes take no input, so nothing validation-shaped can reach them
-- same two-tier exception mapping (Dependency/Service only) as Review's
GET /review/flags, which has the identical shape for the identical reason.

C1/C3 return their dataclasses via asdict() rather than a hand-built dict:
neither SpeakingTotal nor UnflaggedStreak carries a datetime, so unlike
/mistakes and /topics there is nothing to isoformat() on the way out. /recap
DOES carry datetimes (session_started_at, session_ended_at) so it needs the
explicit isoformat() dict the way /mistakes and /topics do -- asdict() alone
would leave those as raw datetime objects, which jsonify() cannot serialize.
"""

from dataclasses import asdict

from flask import Blueprint, jsonify

from api.models.aggregations.session_recap.exceptions import (
    SessionRecapAggregationDependencyException,
    SessionRecapAggregationServiceException,
)
from api.models.orchestrations.progress.exceptions import (
    ProgressOrchestrationDependencyException,
    ProgressOrchestrationServiceException,
)
from api.services.aggregations.session_recap import SessionRecapAggregationService
from api.services.orchestrations.progress import ProgressOrchestrationService


def make_progress_blueprint(
    orchestrator: ProgressOrchestrationService,
    recap_aggregator: SessionRecapAggregationService,
) -> Blueprint:
    progress_blueprint = Blueprint("progress", __name__, url_prefix="/progress")

    @progress_blueprint.route("/mistakes", methods=["GET"])
    def list_mistakes():
        try:
            patterns = orchestrator.list_mistake_summary()
            # A1's interval_days/next_due_at are scheduler-internal: dropped here so
            # the /mistakes wire contract (and the frontend) stay unchanged.
            payload = [
                {
                    **{k: v for k, v in asdict(p).items() if k not in ("interval_days", "next_due_at")},
                    "last_seen_at": p.last_seen_at.isoformat(),
                }
                for p in patterns
            ]
            return jsonify(payload), 200
        except ProgressOrchestrationDependencyException as e:
            return jsonify({"error": str(e.inner_exception)}), 500
        except ProgressOrchestrationServiceException as e:
            return jsonify({"error": str(e.inner_exception)}), 500

    @progress_blueprint.route("/topics", methods=["GET"])
    def list_topics():
        try:
            entries = orchestrator.list_topic_coverage()
            return (
                jsonify(
                    [
                        {
                            "topic": e.topic,
                            "covered": e.covered,
                            "first_covered_at": e.first_covered_at.isoformat() if e.first_covered_at else None,
                        }
                        for e in entries
                    ]
                ),
                200,
            )
        except ProgressOrchestrationDependencyException as e:
            return jsonify({"error": str(e.inner_exception)}), 500
        except ProgressOrchestrationServiceException as e:
            return jsonify({"error": str(e.inner_exception)}), 500

    @progress_blueprint.route("/speaking", methods=["GET"])
    def get_speaking():
        try:
            return jsonify(asdict(orchestrator.get_speaking_total())), 200
        except ProgressOrchestrationDependencyException as e:
            return jsonify({"error": str(e.inner_exception)}), 500
        except ProgressOrchestrationServiceException as e:
            return jsonify({"error": str(e.inner_exception)}), 500

    @progress_blueprint.route("/streak", methods=["GET"])
    def get_streak():
        try:
            return jsonify(asdict(orchestrator.get_longest_unflagged_streak())), 200
        except ProgressOrchestrationDependencyException as e:
            return jsonify({"error": str(e.inner_exception)}), 500
        except ProgressOrchestrationServiceException as e:
            return jsonify({"error": str(e.inner_exception)}), 500

    @progress_blueprint.route("/recap", methods=["GET"])
    def get_recap():
        # No session ever having completed is a normal state, not an error
        # -- same "empty is not a failure" call this file already makes for
        # /mistakes and /topics, and Review makes for GET /review/flags.
        # Unlike /speaking and /streak there is no sensible zero-valued
        # SessionRecap to fall back to (no session means no boundary
        # timestamps to report), so this returns `null` with 200 rather than
        # inventing placeholder dates.
        try:
            recap = recap_aggregator.get_latest_recap()
            if recap is None:
                return jsonify(None), 200
            body = {
                **asdict(recap),
                "session_started_at": recap.session_started_at.isoformat(),
                "session_ended_at": recap.session_ended_at.isoformat() if recap.session_ended_at else None,
            }
            return jsonify(body), 200
        except SessionRecapAggregationDependencyException as e:
            return jsonify({"error": str(e.inner_exception)}), 500
        except SessionRecapAggregationServiceException as e:
            return jsonify({"error": str(e.inner_exception)}), 500

    return progress_blueprint
