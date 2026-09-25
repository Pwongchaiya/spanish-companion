"""Relocated from mistake_pattern_processing_service.py's __main__ self-check
-- production files don't carry test code, matching
NL.Core.Users.Api.Tests.Unit being a separate tree from NL.Core.Users.Api.
"""

from datetime import datetime
from unittest.mock import Mock

from api.models.foundations.mistake_pattern.exceptions import NotFoundMistakePatternException
from api.models.foundations.mistake_pattern.mistake_pattern import MistakePattern
from api.services.processings.mistake_pattern.mistake_pattern_processing_service import (
    MistakePatternProcessingService,
)


def test_mistake_pattern_processing_service():
    existing = MistakePattern(
        id=1, profile_id=1, category="ser vs estar", occurrence_count=2, last_seen_at=datetime.now(), status="resolved"
    )

    # record_occurrence: found -> increment + reactivate
    foundation = Mock()
    foundation.list_mistake_patterns_by_profile.return_value = [existing]
    incremented = MistakePattern(
        id=1, profile_id=1, category="ser vs estar", occurrence_count=3, last_seen_at=datetime.now(), status="active"
    )
    foundation.update_mistake_pattern.return_value = incremented
    service = MistakePatternProcessingService(foundation)

    assert service.record_occurrence(1, "ser vs estar") is incremented
    foundation.update_mistake_pattern.assert_called_once_with(1, occurrence_count=3, status="active")
    foundation.create_mistake_pattern.assert_not_called()

    # record_occurrence: not found -> create
    foundation = Mock()
    foundation.list_mistake_patterns_by_profile.return_value = []
    created = MistakePattern(
        id=2,
        profile_id=1,
        category="gender agreement",
        occurrence_count=1,
        last_seen_at=datetime.now(),
        status="active",
    )
    foundation.create_mistake_pattern.return_value = created
    service = MistakePatternProcessingService(foundation)

    assert service.record_occurrence(1, "gender agreement") is created
    foundation.create_mistake_pattern.assert_called_once_with(1, "gender agreement")
    foundation.update_mistake_pattern.assert_not_called()

    # resolve: found -> update with status="resolved", same occurrence_count
    active = MistakePattern(
        id=3, profile_id=1, category="subjunctive", occurrence_count=4, last_seen_at=datetime.now(), status="active"
    )
    foundation = Mock()
    foundation.list_mistake_patterns_by_profile.return_value = [active]
    resolved = MistakePattern(
        id=3, profile_id=1, category="subjunctive", occurrence_count=4, last_seen_at=datetime.now(), status="resolved"
    )
    foundation.update_mistake_pattern.return_value = resolved
    service = MistakePatternProcessingService(foundation)

    assert service.resolve(1, "subjunctive") is resolved
    foundation.update_mistake_pattern.assert_called_once_with(3, occurrence_count=4, status="resolved")

    # resolve: not found -> raises
    foundation = Mock()
    foundation.list_mistake_patterns_by_profile.return_value = []
    service = MistakePatternProcessingService(foundation)

    try:
        service.resolve(1, "no such category")
        raise AssertionError("expected NotFoundMistakePatternException")
    except NotFoundMistakePatternException:
        pass
    foundation.update_mistake_pattern.assert_not_called()
