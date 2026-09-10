"""Integration tests for ReviewOrchestrator's real file I/O.

Review has two kinds of dependency and they get different treatment here:

- FlagService / PracticeLogService are real, built over real local JSON /
  JSON Lines brokers -- cheap, and the one thing the Unit tier's mocks
  genuinely cannot confirm (does a flag written by save_flags() actually come
  back out of list_flags(); does record_practice() actually leave a readable
  line on disk). So they are REAL, pointed at pytest's tmp_path rather than
  the default data/ paths.

- HybridRetrievalService / GenerationService wrap Retrieval (Postgres +
  embedding model) and Generation (Gemini). Both already have their own
  Integration tiers; exercising them again through Review would be duplicate
  coverage of someone else's feature, so they stay mocked.

No Postgres, so no TEST_DATABASE_URL and no chunk_repository fixture --
tests/integration/conftest.py's fixture is simply not requested here.
"""

from datetime import datetime
from unittest.mock import Mock

import pytest

from api.brokers.flag import JsonFileFlagBroker
from api.brokers.logging import StdlibLoggingBroker
from api.brokers.practice_log import JsonLinesPracticeLogBroker
from api.models.flag import Flag
from api.models.flag.exceptions import FlagValidationException, NotFoundFlagException
from api.models.review.exceptions import ReviewOrchestrationValidationException
from api.services.foundations.flag import FlagService
from api.services.foundations.practice_log import PracticeLogService
from api.services.orchestrations.review import ReviewOrchestrator
from rag.models.generation import Explanation
from rag.models.retrieval import ScoredChunk
from rag.services.foundations.generation import GenerationService
from rag.services.orchestrations.retrieval import HybridRetrievalService

FIXED_NOW = datetime(2026, 1, 2, 3, 4, 5)
RETRIEVAL_TOP_K = 3


class FakeConfigurationBroker:
    """Dict-backed ConfigurationBroker stub -- fixed, known config values."""

    def __init__(self, values: dict) -> None:
        self._values = values

    def get(self, key: str, default: str | None = None) -> str | None:
        return self._values.get(key, default)

    def require(self, key: str) -> str:
        return self._values[key]


@pytest.fixture
def flag_broker(tmp_path):
    # path= explicitly, never the env-configured default -- a test must not be
    # able to read or clobber the real data/flags.json.
    return JsonFileFlagBroker(path=tmp_path / "flags.json")


@pytest.fixture
def practice_log_broker(tmp_path):
    return JsonLinesPracticeLogBroker(path=tmp_path / "practice_log.jsonl")


@pytest.fixture
def flag_service(flag_broker):
    return FlagService(flag_broker=flag_broker, logging_broker=StdlibLoggingBroker())


@pytest.fixture
def practice_log_service(practice_log_broker):
    return PracticeLogService(practice_log_broker=practice_log_broker, logging_broker=StdlibLoggingBroker())


@pytest.fixture
def mock_retrieval_service():
    return Mock(spec=HybridRetrievalService)


@pytest.fixture
def mock_generation_service():
    return Mock(spec=GenerationService)


@pytest.fixture
def service(flag_service, practice_log_service, mock_retrieval_service, mock_generation_service):
    return ReviewOrchestrator(
        flag_service=flag_service,
        practice_log_service=practice_log_service,
        retrieval_service=mock_retrieval_service,
        generation_service=mock_generation_service,
        clock=lambda: FIXED_NOW,
        logging_broker=StdlibLoggingBroker(),
        configuration_broker=FakeConfigurationBroker({"RETRIEVAL_TOP_K": str(RETRIEVAL_TOP_K)}),
    )


def make_flag(flag_id: str, corrected: str = "fui al mercado", category: str = "preterite") -> Flag:
    return Flag(
        id=flag_id,
        said="iba al mercado ayer",
        corrected=corrected,
        category=category,
        timestamp=FIXED_NOW,
    )


class TestReviewOrchestratorIntegration:

    def test_should_list_exactly_the_flags_written_to_the_real_file(self, service, flag_broker):
        # given
        flags = [make_flag("flag-1"), make_flag("flag-2", corrected="comí", category="accents")]
        flag_broker.save_flags(flags)

        # when
        actual = service.list_flags()

        # then -- a real JSON round-trip, not a mock's return value
        assert actual == flags

    def test_should_list_no_flags_when_the_file_was_never_written(self, service):
        assert service.list_flags() == []

    def test_should_append_a_readable_line_to_the_real_practice_log(self, service, flag_broker, practice_log_broker):
        # given
        flag_broker.save_flags([make_flag("flag-1"), make_flag("flag-2")])

        # when
        first = service.record_practice("flag-1", "fui al mercado ayer")
        second = service.record_practice("flag-2", "comí demasiado")

        # then -- read back off disk, through the broker's own read path
        assert practice_log_broker.read_attempts() == [first, second]
        assert practice_log_broker.read_attempts(flag_id="flag-2") == [second]

    def test_should_explain_the_top_chunk_for_a_flag_loaded_from_the_real_file(
        self, service, flag_broker, mock_retrieval_service, mock_generation_service
    ):
        # given
        flag = make_flag("flag-1", corrected="fui al mercado", category="preterite")
        flag_broker.save_flags([flag])

        top_chunk = ScoredChunk(
            chunk_id=10,
            topic="preterite vs imperfect",
            source_url="https://rae.example/10",
            content="...",
            score=0.9,
        )
        mock_retrieval_service.retrieve.return_value = [top_chunk]
        expected = Explanation(explanation="grounded answer", source_url=top_chunk.source_url)
        mock_generation_service.explain.return_value = expected

        # when
        actual = service.explain_flag("flag-1")

        # then
        assert actual is expected
        mock_retrieval_service.retrieve.assert_called_once_with(
            query="fui al mercado",
            top_k=RETRIEVAL_TOP_K,
            category="preterite",
        )
        # The flag handed to Generation is the one reconstructed from disk.
        mock_generation_service.explain.assert_called_once_with(flag, top_chunk)

    def test_should_raise_validation_exception_when_the_real_file_has_no_such_id(
        self, service, flag_broker, mock_retrieval_service, practice_log_broker
    ):
        # given
        flag_broker.save_flags([make_flag("flag-1")])

        # when / then -- FlagService wraps its NotFoundFlagException leaf, and
        # Review carries that wrapper through whole, so the leaf is two levels
        # deep rather than one.
        for call in (
            lambda: service.explain_flag("does-not-exist"),
            lambda: service.record_practice("does-not-exist", "fui al mercado"),
        ):
            with pytest.raises(ReviewOrchestrationValidationException) as exc_info:
                call()
            assert isinstance(exc_info.value.inner_exception, FlagValidationException)
            assert isinstance(exc_info.value.inner_exception.inner_exception, NotFoundFlagException)

        mock_retrieval_service.retrieve.assert_not_called()
        assert practice_log_broker.read_attempts() == []
