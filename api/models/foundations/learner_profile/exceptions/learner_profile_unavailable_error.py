"""Leaf dependency exception raised when a LearnerProfileBroker call fails."""

from api.errors import ApiError


class LearnerProfileUnavailableError(ApiError):
    """Raised when select_profile()/insert_profile()/update_profile() raises.

    Name and shape mirror FlagUnavailableError -- names "the broker behind
    this is down", not a legitimate empty result (select_profile()
    returning None is not this; that's NotFoundLearnerProfileException,
    a validation-tier condition, not a dependency failure).

    Leaf exception -- always caught and wrapped into
    LearnerProfileDependencyException before leaving LearnerProfileService.
    """
