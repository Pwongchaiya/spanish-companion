"""Shared base for all rag-layer exceptions.

Lets Exposer controllers catch one type instead of enumerating every
feature's exception class.
"""

from common.errors import BaseError


class RagError(BaseError):
    """Base for all exceptions raised within the rag package."""
