"""Shared fixtures for SessionRecapAggregationService unit tests.

Per CLAUDE.md's Phase 2 test strategy: both dependencies are mocked via
unittest.mock.Mock(spec=...) at their Protocol boundary -- never the real
Review/Progress orchestrators, which would drag in Postgres/rag.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from api.services.aggregations.session_recap.session_recap_aggregation_service import (
    SessionRecapAggregationService,
)
from api.services.foundations.tts.i_tts_service import ITtsService
from api.services.orchestrations.progress.i_progress_service import ProgressService
from api.services.orchestrations.review.i_review_service import ReviewService
from tests.unit.services._api_logging_fixture import mock_logging_broker  # noqa: F401

FIXED_NOW = datetime(2026, 9, 18, 18, 0, 0)


@pytest.fixture
def mock_review_service():
    return Mock(spec=ReviewService)


@pytest.fixture
def mock_progress_service():
    return Mock(spec=ProgressService)


@pytest.fixture
def mock_tts_service():
    return Mock(spec=ITtsService)


@pytest.fixture
def service(mock_review_service, mock_progress_service, mock_tts_service, mock_logging_broker):
    return SessionRecapAggregationService(
        mock_review_service,
        mock_progress_service,
        mock_tts_service,
        logging_broker=mock_logging_broker,
    )


@pytest.fixture
def make_session_log_entry():
    def _make(entry_id: int = 1, minutes: float | None = 20.0, flag_count: int = 2):
        started_at = FIXED_NOW
        ended_at = None if minutes is None else started_at + timedelta(minutes=minutes)
        return Mock(id=entry_id, started_at=started_at, ended_at=ended_at, flag_count=flag_count)

    return _make


@pytest.fixture
def make_flag():
    def _make(category: str, flag_id: str = "abc123"):
        return Mock(id=flag_id, category=category)

    return _make
