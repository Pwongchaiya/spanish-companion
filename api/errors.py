"""Marker base for all api-layer exceptions.

Lets Exposer controllers catch one type instead of enumerating every
feature's exception class. Purely a marker — no behavior of its own.
"""


class ApiError(Exception):
    """Base for all exceptions raised within the api package."""
