"""Shared base for all api-layer exceptions.

Lets Exposer controllers catch one type instead of enumerating every
feature's exception class.
"""

from typing import Optional


class ApiError(Exception):
    """Base for all exceptions raised within the api package.

    Optionally carries `inner_exception`, matching NL.Core.Entitlements'
    Xeption(message, innerException) base
    (NL.Core.Entitlements.Api/Models/Foundations/Entitlements/Exceptions/
    EntitlementValidationException.cs:11-13) -- wrapper-tier exceptions set
    this to the leaf exception they're wrapping; leaf exceptions leave it
    None.
    """

    def __init__(self, message: str, inner_exception: Optional[Exception] = None) -> None:
        super().__init__(message)
        self.inner_exception = inner_exception
