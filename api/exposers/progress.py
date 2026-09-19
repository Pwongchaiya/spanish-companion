"""Flask Blueprint exposing Progress (roadmap Phase 2: A5/F1/C1/C3) over HTTP.

Thin mapping layer only -- see api/services/orchestrations/progress/ for the
actual mistake-summary / topic-coverage / speaking-total / unflagged-streak
reads this wraps. Routes are
unversioned per CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers
(/api/V1.0/ is waived), prefixed /progress.

ProgressOrchestrationService is constructed from its dependencies by
api/app.py and injected here via make_progress_blueprint(). This module
never constructs the orchestrator or any of its dependencies itself.

Origin/Referer CSRF-shaped checking is NOT implemented here -- it lives
app-wide in api/app.py, applied uniformly across every route.

All four routes take no input, so nothing validation-shaped can reach them
-- same two-tier exception mapping (Dependency/Service only) as Review's
GET /review/flags, which has the identical shape for the identical reason.

C1/C3 return their dataclasses via asdict() rather than a hand-built dict:
neither SpeakingTotal nor UnflaggedStreak carries a datetime, so unlike
/mistakes and /topics there is nothing to isoformat() on the way out.
"""

from dataclasses import asdict

from flask import Blueprint, jsonify

from api.models.orchestrations.progress.exceptions import (
    ProgressOrchestrationDependencyException,
    ProgressOrchestrationServiceException,
)
from api.services.orchestrations.progress import ProgressOrchestrationService


def make_progress_blueprint(orchestrator: ProgressOrchestrationService) -> Blueprint:
    progress_blueprint = Blueprint("progress", __name__, url_prefix="/progress")

    @progress_blueprint.route("/mistakes", methods=["GET"])
    def list_mistakes():
        try:
            patterns = orchestrator.list_mistake_summary()
            return jsonify([{**asdict(p), "last_seen_at": p.last_seen_at.isoformat()} for p in patterns]), 200
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

    return progress_blueprint
