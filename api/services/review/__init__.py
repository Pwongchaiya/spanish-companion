from api.services.review.i_review_service import ReviewService
from api.services.review.review_service import _ReviewOrchestratorBase, RETRIEVAL_TOP_K
from api.services.review.review_service_validations import ReviewOrchestratorValidations
from api.services.review.review_service_exceptions import ReviewOrchestratorExceptions


class ReviewOrchestrator(
    _ReviewOrchestratorBase,
    ReviewOrchestratorValidations,
    ReviewOrchestratorExceptions,
):
    """Combines the base logic, validations, and exceptions mixins into the
    concrete Orchestration service -- mirrors C#'s `partial class` merging
    EntitlementCodesOrchestrationService.cs / .Validations.cs / .Exeptions.cs
    into one class.
    """


__all__ = [
    "ReviewService",
    "ReviewOrchestrator",
    "RETRIEVAL_TOP_K",
]
