"""record_review(): unknown grade is rejected before any Foundation call."""

from unittest.mock import Mock

import pytest

from api.models.foundations.mistake_pattern.exceptions import InvalidMistakePatternException
from api.services.foundations.mistake_pattern.i_mistake_pattern_service import IMistakePatternService
from api.services.processings.mistake_pattern.mistake_pattern_processing_service import (
    MistakePatternProcessingService,
)


class TestMistakePatternProcessingServiceRecordReviewValidation:

    @pytest.mark.parametrize("bad_grade", [None, "", "GOOD", "perfect"])
    def test_should_raise_invalid_when_grade_is_unknown(self, bad_grade):
        # given
        foundation = Mock(spec=IMistakePatternService)
        service = MistakePatternProcessingService(foundation)

        # when / then
        with pytest.raises(InvalidMistakePatternException) as caught:
            service.record_review(1, "ser vs estar", bad_grade)

        assert "grade" in caught.value.errors
        foundation.list_mistake_patterns_by_profile.assert_not_called()
        foundation.update_mistake_pattern.assert_not_called()
