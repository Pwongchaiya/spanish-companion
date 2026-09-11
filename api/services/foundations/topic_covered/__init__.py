from api.services.foundations.topic_covered.i_topic_covered_service import ITopicCoveredService
from api.services.foundations.topic_covered.topic_covered_service import _TopicCoveredServiceBase
from api.services.foundations.topic_covered.topic_covered_service_validations import (
    TopicCoveredServiceValidations,
)
from api.services.foundations.topic_covered.topic_covered_service_exceptions import (
    TopicCoveredServiceExceptions,
)


class TopicCoveredService(
    _TopicCoveredServiceBase,
    TopicCoveredServiceValidations,
    TopicCoveredServiceExceptions,
):
    """Combines the base logic, validations, and exceptions mixins into the
    concrete Foundation service -- mirrors C#'s `partial class` merging
    EntitlementService.cs / .Validations.cs / .Exceptions.cs into one class,
    the same multi-inheritance-merge already used for LearnerProfile in
    this codebase.
    """


__all__ = [
    "ITopicCoveredService",
    "TopicCoveredService",
]
