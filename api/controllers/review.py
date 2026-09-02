"""Flask Blueprint exposing Review Mode over HTTP.

Thin mapping layer only -- see api/services/review/ for the actual
flagged-list -> selection -> grounded-explanation -> practice-attempt flow
this wraps. Routes are unversioned per CLAUDE.md's Phase 2 Layer-Agent
Mapping & Waivers (/api/V1.0/ is waived), prefixed /review per the
architecture decision record's /review* naming.

ReviewOrchestrator is constructed from its dependencies by api/app.py and
injected here via make_review_blueprint(). This module never constructs the
orchestrator or any of its dependencies itself.

Origin/Referer CSRF-shaped checking is NOT implemented here -- it lives
app-wide in api/app.py, applied uniformly across /start /stop /status and
/review*.

Exception mapping mirrors NL.Core.Entitlements.Api/Controllers/
EntitlementCodesController.cs:30-52: the service now raises wrapper
exceptions only (ReviewOrchestrationValidationException /
...DependencyException / ...ServiceException), never a leaf directly, so
this controller never catches a leaf. C#'s `catch (X) when (cond)`
exception filter has no Python equivalent -- it's translated as a single
`except ReviewOrchestrationValidationException` block with an
`isinstance(e.inner_exception, ...)` check inside, matching
api/controllers/session_lifecycle.py. The response body is built from
`e.inner_exception` (the wrapped leaf), not from `e` itself, matching the
C# pattern of returning `...ValidationException.InnerException`.

The attempt_text blank check that used to live inline here now lives in the
service (ReviewOrchestratorValidations._validate_practice_input) and
arrives as InvalidReviewOrchestrationException inside the validation
wrapper -- same 400, same body text, one layer down.
"""

from dataclasses import asdict

from flask import Blueprint, jsonify, request

from api.models.flag.exceptions import NotFoundFlagException
from api.models.review.exceptions import (
    ReviewOrchestrationDependencyException,
    ReviewOrchestrationServiceException,
    ReviewOrchestrationValidationException,
)
from api.services.orchestrations.review import ReviewOrchestrator


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
        except ReviewOrchestrationValidationException as e:
            if isinstance(e.inner_exception, NotFoundFlagException):
                return jsonify({"error": str(e.inner_exception)}), 404
            return jsonify({"error": str(e.inner_exception)}), 400
        except ReviewOrchestrationDependencyException as e:
            return jsonify({"error": str(e.inner_exception)}), 500
        except ReviewOrchestrationServiceException as e:
            return jsonify({"error": str(e.inner_exception)}), 500

    @review_blueprint.route("/flags/<flag_id>/practice", methods=["POST"])
    def record_practice(flag_id: str):
        body = request.get_json(silent=True) or {}
        attempt_text = body.get("attempt_text")
        try:
            attempt = orchestrator.record_practice(flag_id, attempt_text)
            return jsonify({**asdict(attempt), "timestamp": attempt.timestamp.isoformat()}), 201
        except ReviewOrchestrationValidationException as e:
            if isinstance(e.inner_exception, NotFoundFlagException):
                return jsonify({"error": str(e.inner_exception)}), 404
            return jsonify({"error": str(e.inner_exception)}), 400
        except ReviewOrchestrationDependencyException as e:
            return jsonify({"error": str(e.inner_exception)}), 500
        except ReviewOrchestrationServiceException as e:
            return jsonify({"error": str(e.inner_exception)}), 500

    return review_blueprint
