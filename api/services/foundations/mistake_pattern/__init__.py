from api.services.foundations.mistake_pattern.i_mistake_pattern_service import IMistakePatternService
from api.services.foundations.mistake_pattern.mistake_pattern_service import _MistakePatternServiceBase
from api.services.foundations.mistake_pattern.mistake_pattern_service_validations import (
    MistakePatternServiceValidations,
)
from api.services.foundations.mistake_pattern.mistake_pattern_service_exceptions import (
    MistakePatternServiceExceptions,
)


class MistakePatternService(
    _MistakePatternServiceBase,
    MistakePatternServiceValidations,
    MistakePatternServiceExceptions,
):
    """Combines the base logic, validations, and exceptions mixins into the
    concrete Foundation service -- mirrors C#'s `partial class` merging
    EntitlementService.cs / .Validations.cs / .Exceptions.cs into one class,
    the same multi-inheritance-merge already used for LearnerProfile in
    this codebase.
    """


__all__ = [
    "IMistakePatternService",
    "MistakePatternService",
]
