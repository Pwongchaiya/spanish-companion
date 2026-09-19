"""Flask Blueprint exposing Review Mode over HTTP.

Thin mapping layer only -- see api/services/review/ for the actual
flagged-list -> selection -> grounded-explanation -> practice-attempt flow
this wraps. Routes are unversioned per CLAUDE.md's Phase 2 Layer-Agent
Mapping & Waivers (/api/V1.0/ is waived), prefixed /review per the
architecture decision record's /review* naming.

ReviewOrchestrationService is constructed from its dependencies by api/app.py and
injected here via make_review_blueprint(). This module never constructs the
orchestrator or any of its dependencies itself.

Origin/Referer CSRF-shaped checking is NOT implemented here -- it lives
app-wide in api/app.py, applied uniformly across /start /stop /status and
/review*.

Every route is wrapped, matching UserProfilesController.cs:25-52. GET
/review/flags carries two tiers rather than four: ReviewOrchestrationService.list_flags()
takes no input, so nothing validation-shaped can reach it, and it has no
NotFoundFlagException case. It was unwrapped entirely until H7 of the
architecture conformance audit.

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

attempt_text is validated at both tiers, deliberately: here, so a malformed
request never reaches the orchestrator at all (test_routes.py's
assert_not_called() on the mock orchestrator enforces this at the HTTP
boundary); again inside PracticeLogService._validate_attempt_text, as
defense-in-depth for any other caller of the service that doesn't go
through this route.
"""

from dataclasses import asdict

from flask import Blueprint, jsonify, request

from api.data.roleplay_scenarios import get_roleplay_scenario
from api.models.foundations.flag.exceptions import NotFoundFlagException
from api.models.orchestrations.review.exceptions import (
    ReviewOrchestrationDependencyException,
    ReviewOrchestrationServiceException,
    ReviewOrchestrationValidationException,
)
from api.services.orchestrations.review import ReviewOrchestrationService


def make_review_blueprint(orchestrator: ReviewOrchestrationService) -> Blueprint:
    review_blueprint = Blueprint("review", __name__, url_prefix="/review")

    @review_blueprint.route("/flags", methods=["GET"])
    def list_flags():
        try:
            flags = orchestrator.list_flags()
            return jsonify([{**asdict(f), "timestamp": f.timestamp.isoformat()} for f in flags]), 200
        except ReviewOrchestrationDependencyException as e:
            return jsonify({"error": str(e.inner_exception)}), 500
        except ReviewOrchestrationServiceException as e:
            return jsonify({"error": str(e.inner_exception)}), 500

    @review_blueprint.route("/task-outcome", methods=["GET"])
    def task_outcome():
        try:
            result = orchestrator.get_task_outcome()
            return jsonify(asdict(result) if result else None), 200
        except ReviewOrchestrationDependencyException as e:
            return jsonify({"error": str(e.inner_exception)}), 500
        except ReviewOrchestrationServiceException as e:
            return jsonify({"error": str(e.inner_exception)}), 500

    @review_blueprint.route("/flags/<flag_id>/explain", methods=["GET"])
    def explain_flag(flag_id: str):
        try:
            explanation = orchestrator.explain_flag(flag_id)
            return jsonify(asdict(explanation)), 200
        except ReviewOrchestrationValidationException as e:
            if isinstance(e.inner_exception.inner_exception, NotFoundFlagException):
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
        if not isinstance(attempt_text, str) or not attempt_text.strip():
            return jsonify({"error": "attempt_text is required"}), 400
        roleplay_slug = body.get("roleplay_slug")
        if roleplay_slug is not None and get_roleplay_scenario(roleplay_slug) is None:
            return jsonify({"error": f"Invalid roleplay_slug: {roleplay_slug!r}"}), 400
        try:
            result = orchestrator.record_practice(flag_id, attempt_text, roleplay_slug)
            body = {
                **asdict(result.attempt),
                "timestamp": result.attempt.timestamp.isoformat(),
                "mastered": result.mastered,
                "grade": result.grade,
            }
            return jsonify(body), 201
        except ReviewOrchestrationValidationException as e:
            if isinstance(e.inner_exception.inner_exception, NotFoundFlagException):
                return jsonify({"error": str(e.inner_exception)}), 404
            return jsonify({"error": str(e.inner_exception)}), 400
        except ReviewOrchestrationDependencyException as e:
            return jsonify({"error": str(e.inner_exception)}), 500
        except ReviewOrchestrationServiceException as e:
            return jsonify({"error": str(e.inner_exception)}), 500

    return review_blueprint
