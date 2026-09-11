"""Leaf validation exception raised when no profile row exists yet."""

from api.errors import ApiError


class NotFoundLearnerProfileException(ApiError):
    """Raised by get_profile() when LearnerProfileBroker.select_profile()
    returns None.

    Foundation is pure CRUD -- it does not create the row on a missing
    read (that's Processing's ensure_profile() get-or-create). Named
    `<Condition><Entity>` per the Flag/Session Lifecycle rebuild convention
    (NotFoundFlagException, AlreadyRunningSessionException).

    Leaf exception -- always caught and wrapped into
    LearnerProfileValidationException before leaving LearnerProfileService.
    """

    def __init__(self) -> None:
        super().__init__("No learner profile exists yet")
