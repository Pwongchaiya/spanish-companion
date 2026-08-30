"""Exposure-tier exception wrapping a validation-tier leaf exception."""

from api.errors import ApiError


class SessionValidationException(ApiError):
    """Wraps a leaf validation-tier exception (AlreadyRunningSessionException
    or NotRunningSessionException) for consumers, without leaking internals.

    Mirrors NL.Core.Entitlements.Api/Models/Foundations/Entitlements/
    Exceptions/EntitlementValidationException.cs:9-14 -- message +
    inner_exception, inner_exception is always the leaf that triggered this.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Session validation error occurred. Fix the errors and try again.",
            inner_exception=inner_exception,
        )
