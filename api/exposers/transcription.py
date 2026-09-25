"""Flask Blueprint exposing free-form transcription over HTTP (review-three-pane HANDOFF.md section 4).

Thin mapping layer only -- see api/services/foundations/transcription/ for the
validate-then-broker-call flow. Route is unversioned per CLAUDE.md's Phase 2
Layer-Agent Mapping & Waivers (/api/V1.0/ is waived).

TranscriptionService is constructed by api/app.py and injected via
make_transcription_blueprint(). Exception mapping mirrors
api/exposers/pronunciation.py: wrapper tiers only, body built from
`str(e.inner_exception)`.

The body is validated here, deliberately, before the service is touched
(tests assert_not_called on it), and again inside TranscriptionService as
defense-in-depth -- same split as pronunciation.py's assess(). The three
400s and WAV_HEADER_BYTES are lifted verbatim from pronunciation.py so both
upload routes validate identically (HANDOFF.md section 4). Upload size is
capped app-wide by MAX_CONTENT_LENGTH (api/app.py), which answers 413 before
this route runs.

`ResultReason.NoMatch` is not an error -- the service returns
Transcription(text="", ...) and this route answers 200, not an error status.
"""

from flask import Blueprint, jsonify, request

from api.models.foundations.transcription.exceptions import (
    TranscriptionDependencyException,
    TranscriptionServiceException,
    TranscriptionValidationException,
)
from api.services.foundations.transcription.i_transcription_service import ITranscriptionService

WAV_HEADER_BYTES = 44


def make_transcription_blueprint(service: ITranscriptionService) -> Blueprint:
    transcription_blueprint = Blueprint("transcription", __name__)

    @transcription_blueprint.route("/transcribe", methods=["POST"])
    def transcribe():
        audio_file = request.files.get("audio")
        audio = audio_file.read() if audio_file is not None else b""
        if not audio:
            return jsonify({"error": "audio file is required"}), 400
        if len(audio) <= WAV_HEADER_BYTES:
            return jsonify({"error": "audio contains no samples"}), 400
        if audio[:4] != b"RIFF" or audio[8:12] != b"WAVE":
            return jsonify({"error": "audio must be a RIFF/WAVE file"}), 400
        try:
            result = service.transcribe(audio)
            return jsonify({"text": result.text, "duration_seconds": result.duration_seconds}), 200
        except TranscriptionValidationException as e:
            return jsonify({"error": str(e.inner_exception)}), 400
        except TranscriptionDependencyException as e:
            return jsonify({"error": str(e.inner_exception)}), 500
        except TranscriptionServiceException as e:
            return jsonify({"error": str(e.inner_exception)}), 500

    return transcription_blueprint


if __name__ == "__main__":
    # ponytail: assert-based self-check for the validation-before-service-call branches
    # (missing/short/non-RIFF audio) -- no pytest tier per MEMORY.md's "no tests during build".
    import io
    from flask import Flask
    from unittest.mock import Mock

    app = Flask(__name__)
    mock_service = Mock(spec=ITranscriptionService)
    app.register_blueprint(make_transcription_blueprint(mock_service))
    client = app.test_client()

    resp = client.post("/transcribe", data={})
    assert resp.status_code == 400 and resp.get_json()["error"] == "audio file is required", resp.get_json()
    mock_service.transcribe.assert_not_called()

    resp = client.post("/transcribe", data={"audio": (io.BytesIO(b"short"), "a.wav")})
    assert resp.status_code == 400 and resp.get_json()["error"] == "audio contains no samples", resp.get_json()
    mock_service.transcribe.assert_not_called()

    junk = b"\x00" * 50
    resp = client.post("/transcribe", data={"audio": (io.BytesIO(junk), "a.wav")})
    assert resp.status_code == 400 and resp.get_json()["error"] == "audio must be a RIFF/WAVE file", resp.get_json()
    mock_service.transcribe.assert_not_called()

    print("ok")
