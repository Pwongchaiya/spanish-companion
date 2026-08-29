"""Flask Blueprint exposing Review Mode over HTTP.

Thin mapping layer only -- see api/services/review.py for the actual
flagged-list -> selection -> grounded-explanation -> practice-attempt flow
this wraps. Routes are unversioned per CLAUDE.md's Phase 2 Layer-Agent
Mapping & Waivers (/api/V1.0/ is waived), prefixed /review per the
architecture decision record's /review* naming.

ReviewOrchestrator is constructed from its four dependencies by api/app.py
(a later step) and injected here via make_review_blueprint(). This module
never constructs the orchestrator or any of its dependencies itself.

Origin/Referer CSRF-shaped checking is NOT implemented here -- it lives
app-wide in api/app.py, applied uniformly across /start /stop /status and
/review*.
"""

from dataclasses import asdict

from flask import Blueprint, jsonify, request

from api.services.review import FlagNotFoundException, ReviewOrchestrator


def make_review_blueprint(orchestrator: ReviewOrchestrator) -> Blueprint:
    review_blueprint = Blueprint("review", __name__, url_prefix="/review")

    @review_blueprint.route("/flags", methods=["GET"])
    def list_flags():
        flags = orchestrator.list_flags()
        return jsonify([{**asdict(f), "timestamp": f.timestamp.isoformat()} for f in flags]), 200

    @review_blueprint.route("/flags/<flag_id>/explain", methods=["GET"])
    def explain_flag(flag_id: str):
        try:
            explanation = orchestrator.explain_flag(flag_id)
            return jsonify(asdict(explanation)), 200
        except FlagNotFoundException as e:
            return jsonify({"error": str(e)}), 404

    @review_blueprint.route("/flags/<flag_id>/practice", methods=["POST"])
    def record_practice(flag_id: str):
        body = request.get_json(silent=True) or {}
        attempt_text = body.get("attempt_text")
        if not isinstance(attempt_text, str) or not attempt_text.strip():
            return jsonify({"error": "attempt_text is required"}), 400
        try:
            attempt = orchestrator.record_practice(flag_id, attempt_text)
            return jsonify({**asdict(attempt), "timestamp": attempt.timestamp.isoformat()}), 201
        except FlagNotFoundException as e:
            return jsonify({"error": str(e)}), 404

    return review_blueprint
