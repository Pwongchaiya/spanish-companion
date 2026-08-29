"""Flask Blueprint exposing the voice-conversation session lifecycle over HTTP.

Thin mapping layer only -- see api/services/session_lifecycle.py for the
actual start/stop/status policy this wraps. Routes are unversioned and
match Phase 1's route names exactly (ui/app.py's /start, /stop), per
CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers (the /api/V1.0/
versioning format is waived for this feature).

ConversationSessionService holds mutable per-session state (the running
subprocess handle, start time, last-stop-graceful flag), so exactly one
instance must be shared across requests -- constructed once by api/app.py
(a later step) and injected here via make_session_lifecycle_blueprint().
This module never constructs the service or its broker itself.

Origin/Referer CSRF-shaped checking is NOT implemented here -- it lives
app-wide in api/app.py, applied uniformly across /start /stop /status and
/review*.
"""

from dataclasses import asdict

from flask import Blueprint, jsonify

from api.services.session_lifecycle import (
    ConversationSessionService,
    SessionAlreadyRunningException,
    SessionNotRunningException,
)


def make_session_lifecycle_blueprint(service: ConversationSessionService) -> Blueprint:
    session_lifecycle_blueprint = Blueprint("session_lifecycle", __name__)

    @session_lifecycle_blueprint.route("/start", methods=["POST"])
    def start():
        try:
            service.start()
            return jsonify(asdict(service.get_status())), 200
        except SessionAlreadyRunningException as e:
            return jsonify({"error": str(e)}), 409

    @session_lifecycle_blueprint.route("/stop", methods=["POST"])
    def stop():
        try:
            service.stop()
            return jsonify(asdict(service.get_status())), 200
        except SessionNotRunningException as e:
            return jsonify({"error": str(e)}), 409

    @session_lifecycle_blueprint.route("/status", methods=["GET"])
    def status():
        return jsonify(asdict(service.get_status())), 200

    return session_lifecycle_blueprint
