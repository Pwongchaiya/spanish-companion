"""Re-exports the concrete TopicCoveredService class, declared directly in
topic_covered_service.py (which inherits the Validations/Exceptions mixins
by name) -- no composition step here, matching MistakePatternService's
one-class-declared-once shape.
"""

from api.services.foundations.topic_covered.i_topic_covered_service import ITopicCoveredService
from api.services.foundations.topic_covered.topic_covered_service import TopicCoveredService

__all__ = [
    "ITopicCoveredService",
    "TopicCoveredService",
]
