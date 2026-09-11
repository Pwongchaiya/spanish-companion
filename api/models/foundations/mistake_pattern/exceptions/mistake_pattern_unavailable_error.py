"""Leaf dependency exception raised when an IMistakePatternBroker call fails."""

from api.errors import ApiError


class MistakePatternUnavailableError(ApiError):
    """Raised when select_by_profile()/insert()/update() raises.

    Name and shape mirror LearnerProfileUnavailableError -- names "the
    broker behind this is down" (including update() against a pattern_id
    that doesn't exist, since the broker has no separate not-found signal
    for that case today).

    Leaf exception -- always caught and wrapped into
    MistakePatternDependencyException before leaving MistakePatternService.
    """
