"""Leaf validation exception raised when a flag status isn't recognised."""

from api.errors import ApiError


class InvalidFlagStatusException(ApiError):
    """Raised by FlagService.save_flags() when a Flag's `status` is not one
    of FLAG_STATUSES ("open" | "mastered" | "skipped").

    Named `Invalid<Field><Entity>` -- same `<Condition><Entity>` shape as
    NotFoundFlagException, the closest existing precedent in this feature.

    Leaf exception -- always caught and wrapped into FlagValidationException
    before leaving FlagService, same as NotFoundFlagException.
    """

    def __init__(self, status: str) -> None:
        super().__init__(f"Invalid flag status: {status!r}")
