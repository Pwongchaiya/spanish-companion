from api.services.foundations.flag.i_flag_service import IFlagService
from api.services.foundations.flag.flag_service import _FlagServiceBase
from api.services.foundations.flag.flag_service_exceptions import FlagServiceExceptions


class FlagService(_FlagServiceBase, FlagServiceExceptions):
    """Combines the base logic and exceptions mixins into the concrete
    Foundation service -- mirrors C#'s `partial class` merging
    EntitlementService.cs / .Exeptions.cs into one class, the same
    multi-inheritance-merge already used for Session Lifecycle and Review
    in this codebase.
    """


__all__ = [
    "IFlagService",
    "FlagService",
]
