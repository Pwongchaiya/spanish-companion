from api.services.foundations.practice_log.i_practice_log_service import IPracticeLogService
from api.services.foundations.practice_log.practice_log_service import _PracticeLogServiceBase
from api.services.foundations.practice_log.practice_log_service_validations import (
    PracticeLogServiceValidations,
)
from api.services.foundations.practice_log.practice_log_service_exceptions import (
    PracticeLogServiceExceptions,
)


class PracticeLogService(
    _PracticeLogServiceBase,
    PracticeLogServiceValidations,
    PracticeLogServiceExceptions,
):
    """Combines the base logic, validations, and exceptions mixins into the
    concrete Foundation service -- mirrors C#'s `partial class` merging
    PracticeLogService.cs / .Validations.cs / .Exeptions.cs into one class.
    """


__all__ = [
    "IPracticeLogService",
    "PracticeLogService",
]
