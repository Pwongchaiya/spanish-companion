"""record_review(): missing pattern raises NotFound; Foundation errors propagate."""

from unittest.mock import Mock

import pytest

from api.models.foundations.mistake_pattern.exceptions import (
    MistakePatternDependencyException,
    NotFoundMistakePatternException,
)
from api.services.foundations.mistake_pattern.i_mistake_pattern_service import IMistakePatternService
from api.services.processings.mistake_pattern.mistake_pattern_processing_service import (
    MistakePatternProcessingService,
)


class TestMistakePatternProcessingServiceRecordReviewExceptions:

    def test_should_raise_not_found_when_no_pattern_exists_for_category(self):
        # given
        foundation = Mock(spec=IMistakePatternService)
        foundation.list_mistake_patterns_by_profile.return_value = []
        service = MistakePatternProcessingService(foundation)

        # when / then
        with pytest.raises(NotFoundMistakePatternException):
            service.record_review(1, "no such category", "good")

        foundation.list_mistake_patterns_by_profile.assert_called_once_with(1)
        foundation.update_mistake_pattern.assert_not_called()

    def test_should_propagate_foundation_dependency_exception_unchanged(self):
        # given
        foundation = Mock(spec=IMistakePatternService)
        expected = MistakePatternDependencyException(inner_exception=Exception("db down"))
        foundation.list_mistake_patterns_by_profile.side_effect = expected
        service = MistakePatternProcessingService(foundation)

        # when / then
        with pytest.raises(MistakePatternDependencyException) as caught:
            service.record_review(1, "ser vs estar", "good")

        assert caught.value is expected
        foundation.update_mistake_pattern.assert_not_called()
