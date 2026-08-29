"""Marker base for all rag-layer exceptions.

Lets Exposer controllers catch one type instead of enumerating every
feature's exception class. Purely a marker — no behavior of its own.
"""


class RagError(Exception):
    """Base for all exceptions raised within the rag package."""
