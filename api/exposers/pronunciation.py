"""Flask Blueprint exposing pronunciation scoring over HTTP (roadmap Phase 4).

Thin mapping layer only -- see api/services/orchestrations/pronunciation/ for
the assess-then-record flow. Route is unversioned per CLAUDE.md's Phase 2
Layer-Agent Mapping & Waivers (/api/V1.0/ is waived).

PronunciationOrchestrationService is constructed by api/app.py and injected
via make_pronunciation_blueprint(). Exception mapping mirrors
api/exposers/review.py:57-111: wrapper tiers only, body built from
`str(e.inner_exception)`.

The body is validated here, deliberately, before the orchestrator is touched
(tests assert_not_called on it), and again inside PronunciationAssessmentService
as defense-in-depth. Upload size is capped app-wide by MAX_CONTENT_LENGTH
(api/app.py), which answers 413 before this route runs.
"""

from flask import Blueprint, jsonify, request

from api.models.orchestrations.pronunciation.exceptions import (
    PronunciationOrchestrationDependencyException,
    PronunciationOrchestrationServiceException,
    PronunciationOrchestrationValidationException,
)
from api.services.foundations.pronunciation_assessment.pronunciation_assessment_service_validations import (
    MAX_REFERENCE_TEXT_LENGTH,
)
from api.services.orchestrations.pronunciation import PronunciationService

WAV_HEADER_BYTES = 44


def make_pronunciation_blueprint(orchestrator: PronunciationService) -> Blueprint:
    pronunciation_blueprint = Blueprint("pronunciation", __name__, url_prefix="/pronunciation")

    @pronunciation_blueprint.route("/assess", methods=["POST"])
    def assess():
        audio_file = request.files.get("audio")
        audio = audio_file.read() if audio_file is not None else b""
        if not audio:
            return jsonify({"error": "audio file is required"}), 400
        if len(audio) <= WAV_HEADER_BYTES:
            return jsonify({"error": "audio contains no samples"}), 400
        if audio[:4] != b"RIFF" or audio[8:12] != b"WAVE":
            return jsonify({"error": "audio must be a RIFF/WAVE file"}), 400
        reference_text = (request.form.get("reference_text") or "").strip()
        if not reference_text:
            return jsonify({"error": "reference_text is required"}), 400
        if len(reference_text) > MAX_REFERENCE_TEXT_LENGTH:
            return jsonify({"error": f"reference_text must be {MAX_REFERENCE_TEXT_LENGTH} characters or fewer"}), 400
        try:
            result = orchestrator.assess_and_record(audio, reference_text)
            return (
                jsonify(
                    {
                        "reference_text": result.reference_text,
                        "accuracy": result.accuracy_score,
                        "fluency": result.fluency_score,
                        "completeness": result.completeness_score,
                        "prosody": result.prosody_score,
                        "overall": result.pronunciation_score,
                        "words": result.words_json,
                        "created_at": result.created_at.isoformat(),
                    }
                ),
                200,
            )
        except PronunciationOrchestrationValidationException as e:
            return jsonify({"error": str(e.inner_exception)}), 400
        except PronunciationOrchestrationDependencyException as e:
            return jsonify({"error": str(e.inner_exception)}), 500
        except PronunciationOrchestrationServiceException as e:
            return jsonify({"error": str(e.inner_exception)}), 500

    return pronunciation_blueprint
