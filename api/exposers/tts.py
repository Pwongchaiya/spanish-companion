"""Flask Blueprint exposing on-demand text-to-speech over HTTP (roadmap
item B6: minimal-pair listening check).

Thin mapping layer only -- see api/services/foundations/tts/tts_service.py
for the actual validate-then-synthesize logic this wraps. Route is
unversioned, matching every other feature's /-prefixed routes per
CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers (/api/V1.0/ is waived).

TtsService is constructed from its broker by api/app.py / api/app_public.py
and injected here via make_tts_blueprint(). This module never constructs
the service or its broker itself.

Exception mapping mirrors api/exposers/session_lifecycle.py's shape: the
service raises wrapper exceptions only (TtsValidationException /
TtsDependencyException / TtsServiceException), never a leaf directly, so
this controller never catches a leaf.

Response is raw WAV bytes with Content-Type: audio/wav, not base64-in-JSON
-- avoids ~33% payload bloat and the frontend can hand the Response body
straight to an <audio> element / Web Audio API without decoding.
"""

from flask import Blueprint, Response, jsonify, request

from api.models.foundations.tts.exceptions import (
    TtsDependencyException,
    TtsServiceException,
    TtsValidationException,
)
from api.services.foundations.tts import TtsService


def make_tts_blueprint(service: TtsService) -> Blueprint:
    tts_blueprint = Blueprint("tts", __name__, url_prefix="/tts")

    @tts_blueprint.route("/synthesize", methods=["POST"])
    def synthesize():
        body = request.get_json(silent=True) or {}
        text = body.get("text")
        rate = body.get("rate", 1.0)
        try:
            audio_bytes = service.synthesize_speech(text, rate)
            return Response(audio_bytes, mimetype="audio/wav")
        except TtsValidationException as e:
            return jsonify({"error": str(e.inner_exception)}), 400
        except TtsDependencyException as e:
            return jsonify({"error": str(e.inner_exception)}), 500
        except TtsServiceException as e:
            return jsonify({"error": str(e.inner_exception)}), 500

    return tts_blueprint
