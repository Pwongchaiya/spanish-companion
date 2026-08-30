"""Leaf validation exception raised by PracticeLogService.record_attempt()."""

from api.errors import ApiError


class InvalidPracticeAttemptException(ApiError):
    """Raised by _validate_attempt_text() when attempt_text is blank.

    New leaf, not a rename -- this is a separate class from
    api.models.review.exceptions.InvalidReviewOrchestrationException, the
    exception it replaces. Same message-only-ctor shape and same fixed
    message (Wave 5 rewires ReviewOrchestrator to call this service instead
    of raising the old leaf directly; the old leaf and its file are left in
    place until that wave retires them -- see this package's dispatch
    notes).

    ponytail: fixed message, no-arg constructor -- same shape as
    AlreadyRunningSessionException / InvalidReviewOrchestrationException.
    Exactly one validated field, so no multi-field accumulator is needed.
    """

    def __init__(self) -> None:
        super().__init__("attempt_text is required")
