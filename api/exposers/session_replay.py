"""Flask Blueprint for transcript replay with aligned audio (roadmap E3).

Thin mapping layer over SessionReplayOrchestrationService. Routes are
unversioned per CLAUDE.md's Exposer waiver, under /review/sessions. Origin/
Referer checking is app-wide in api/app.py's before_request, so both routes
here pass through it like every other route; nothing is re-checked here.

  GET /review/sessions/<id>/replay -> {session_log_id, duration_seconds,
        audio_url, flags: [{flag_id, offset_seconds, said, corrected, category, status}]}
  GET /review/sessions/latest      -> {session_log_id} of the newest recording, 404 if none
                                      (extra to the pinned contract; see get_latest)
  GET /review/sessions/<id>/audio  -> the WAV (audio/wav, range-capable so the
        <audio> element can seek); 404 when there is no recording.

Exception mapping follows api/exposers/review.py. The 404 case (no recording,
or no such session) sits at different depths of the wrapper chain, so
`_is_not_found` walks `inner_exception` rather than hard-coding one depth.
"""

from pathlib import Path

from flask import Blueprint, jsonify, send_file

from api.models.foundations.session_audio.exceptions import NotFoundSessionAudioException
from api.models.orchestrations.session_replay.exceptions import (
    NotFoundSessionReplayException,
    SessionReplayOrchestrationDependencyException,
    SessionReplayOrchestrationServiceException,
    SessionReplayOrchestrationValidationException,
)
from api.services.orchestrations.session_replay import ISessionReplayService


def _is_not_found(error: Exception) -> bool:
    current = error
    while current is not None:
        if isinstance(current, (NotFoundSessionAudioException, NotFoundSessionReplayException)):
            return True
        current = getattr(current, "inner_exception", None)
    return False


def make_session_replay_blueprint(orchestrator: ISessionReplayService) -> Blueprint:
    blueprint = Blueprint("session_replay", __name__, url_prefix="/review/sessions")

    @blueprint.route("/latest", methods=["GET"])
    def get_latest():
        # Not in the pinned E3 contract: the Review tab has no other way to learn
        # which session_log_id to replay. Additive; the pinned routes are unchanged.
        try:
            return jsonify({"session_log_id": orchestrator.get_latest_session_id()}), 200
        except SessionReplayOrchestrationValidationException as e:
            return jsonify({"error": str(e.inner_exception)}), 404 if _is_not_found(e) else 400
        except SessionReplayOrchestrationDependencyException as e:
            return jsonify({"error": str(e.inner_exception)}), 500
        except SessionReplayOrchestrationServiceException as e:
            return jsonify({"error": str(e.inner_exception)}), 500

    @blueprint.route("/<int:session_log_id>/replay", methods=["GET"])
    def get_replay(session_log_id: int):
        try:
            replay = orchestrator.get_replay(session_log_id)
            return (
                jsonify(
                    {
                        "session_log_id": replay.session_log_id,
                        "duration_seconds": replay.duration_seconds,
                        "audio_url": f"/review/sessions/{replay.session_log_id}/audio",
                        "flags": [
                            {
                                "flag_id": f.flag_id,
                                "offset_seconds": f.offset_seconds,
                                "said": f.said,
                                "corrected": f.corrected,
                                "category": f.category,
                                "status": f.status,
                            }
                            for f in replay.flags
                        ],
                    }
                ),
                200,
            )
        except SessionReplayOrchestrationValidationException as e:
            return jsonify({"error": str(e.inner_exception)}), 404 if _is_not_found(e) else 400
        except SessionReplayOrchestrationDependencyException as e:
            return jsonify({"error": str(e.inner_exception)}), 500
        except SessionReplayOrchestrationServiceException as e:
            return jsonify({"error": str(e.inner_exception)}), 500

    @blueprint.route("/<int:session_log_id>/audio", methods=["GET"])
    def get_audio(session_log_id: int):
        try:
            audio = orchestrator.get_audio(session_log_id)
        except SessionReplayOrchestrationValidationException as e:
            return jsonify({"error": str(e.inner_exception)}), 404 if _is_not_found(e) else 400
        except SessionReplayOrchestrationDependencyException as e:
            return jsonify({"error": str(e.inner_exception)}), 500
        except SessionReplayOrchestrationServiceException as e:
            return jsonify({"error": str(e.inner_exception)}), 500
        # ponytail: the row can outlive its file (manual delete, retention race) -- 404, not 500.
        if not Path(audio.file_path).is_file():
            return jsonify({"error": "audio file is missing"}), 404
        return send_file(audio.file_path, mimetype="audio/wav", conditional=True)

    return blueprint
