"""Leaf exception raised when a (profile_id, category) row already exists.

A race, not a broken system: Processing's find-by-category check
(list_by_profile then filter) and MistakePatternService.create() aren't
atomic, so two concurrent record_occurrence() calls for the same category
can both pass the find-by-category check and both call create(). The DB's
unique constraint is the backstop -- this is the leaf raised when it fires.

Mirrors NL.Core.Users' DuplicateKeyException -> AlreadyExistsUserProfileException
pairing (UserProfileService.Exceptions.cs:46-53): a business-rule conflict
detected via the DB, not an input-shape problem, so it's wrapped into
MistakePatternDependencyValidationException (not MistakePatternValidationException)
before leaving the service.
"""

from api.errors import ApiError


class AlreadyExistsMistakePatternException(ApiError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
