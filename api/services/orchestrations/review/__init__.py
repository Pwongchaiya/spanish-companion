from api.services.orchestrations.review.i_review_service import ReviewService
from api.services.orchestrations.review.review_service import _ReviewOrchestrationServiceBase
from api.services.orchestrations.review.review_service_exceptions import ReviewOrchestrationServiceExceptions


class ReviewOrchestrationService(
    _ReviewOrchestrationServiceBase,
    ReviewOrchestrationServiceExceptions,
):
    """Combines the base logic and exceptions mixins into the concrete
    Orchestration service -- mirrors C#'s `partial class` merging
    EntitlementCodesOrchestrationService.cs / .Exeptions.cs into one class.

    No Validations mixin: nothing is validated at this tier any more. The
    blank attempt_text check moved down to PracticeLogService.
    """


__all__ = [
    "ReviewService",
    "ReviewOrchestrationService",
]
