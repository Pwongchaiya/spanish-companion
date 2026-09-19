"""Shared base for all api-layer exceptions.

Lets Exposer controllers catch one type instead of enumerating every
feature's exception class.
"""

from common.errors import BaseError


class ApiError(BaseError):
    """Base for all exceptions raised within the api package."""
