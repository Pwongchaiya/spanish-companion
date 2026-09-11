"""Validation checks for TopicCoveredService.

Mirrors LearnerProfileServiceValidations's shape -- a private method
containing a single `if (condition): raise LeafException()` check, called
from the base service file's public-method bodies rather than inlined
there.
"""

from api.models.foundations.topic_covered.exceptions import InvalidTopicCoveredInputError


class TopicCoveredServiceValidations:
    """Mixin: raises the leaf exceptions when input doesn't pass checks.
    See topic_covered_service_exceptions.py for how these get wrapped and
    logged before leaving the service.
    """

    def _validate_topic(self, topic: str | None) -> None:
        if topic is None or not topic.strip():
            raise InvalidTopicCoveredInputError(topic)
