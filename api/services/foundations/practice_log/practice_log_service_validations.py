"""Validation checks for PracticeLogService.

Verbatim port of ReviewOrchestratorValidations._validate_practice_input
(api/services/review/review_service_validations.py) -- absorbed here per
this wave's dispatch (the check moves to the new Foundation service; Wave 5
rewires ReviewOrchestrationService to call this service instead of validating the
same field itself).
"""

from api.models.foundations.practice_log.exceptions import InvalidPracticeAttemptException


class PracticeLogServiceValidations:
    """Mixin: raises the leaf validation exception when caller input is
    unusable. See practice_log_service_exceptions.py for how this gets
    wrapped and logged before leaving the service.
    """

    def _validate_attempt_text(self, attempt_text: str) -> None:
        if not isinstance(attempt_text, str) or not attempt_text.strip():
            raise InvalidPracticeAttemptException()
