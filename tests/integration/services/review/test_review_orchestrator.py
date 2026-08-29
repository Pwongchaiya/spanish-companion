"""Integration tests for ReviewOrchestrator's real file I/O.

Review has two kinds of dependency and they get different treatment here:

- FlagBroker / PracticeLogBroker are real local JSON / JSON Lines files --
  cheap, and the one thing the Unit tier's mocks genuinely cannot confirm
  (does a flag written by save_flags() actually come back out of load_flags();
  does record_practice() actually leave a readable line on disk). So they are
  REAL, pointed at pytest's tmp_path rather than the default data/ paths.

- RetrievalController / GenerationController wrap Retrieval (Postgres +
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
from api.brokers.practice_log import JsonLinesPracticeLogBroker
from api.models.flag import Flag
from api.services.review import RETRIEVAL_TOP_K, FlagNotFoundException, ReviewOrchestrator
from rag.controllers.generation import GenerationController
from rag.controllers.retrieval import RetrievalController
from rag.models.generation import Explanation
from rag.models.retrieval import ScoredChunk

FIXED_NOW = datetime(2026, 1, 2, 3, 4, 5)


@pytest.fixture
def flag_broker(tmp_path):
    # path= explicitly, never the env-configured default -- a test must not be
    # able to read or clobber the real data/flags.json.
    return JsonFileFlagBroker(path=tmp_path / "flags.json")


@pytest.fixture
def practice_log_broker(tmp_path):
    return JsonLinesPracticeLogBroker(path=tmp_path / "practice_log.jsonl")


@pytest.fixture
def mock_retrieval_controller():
    return Mock(spec=RetrievalController)


@pytest.fixture
def mock_generation_controller():
    return Mock(spec=GenerationController)


@pytest.fixture
def service(flag_broker, practice_log_broker, mock_retrieval_controller, mock_generation_controller):
    return ReviewOrchestrator(
        flag_broker=flag_broker,
        practice_log_broker=practice_log_broker,
        retrieval_controller=mock_retrieval_controller,
        generation_controller=mock_generation_controller,
        clock=lambda: FIXED_NOW,
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
        self, service, flag_broker, mock_retrieval_controller, mock_generation_controller
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
        mock_retrieval_controller.retrieve.return_value = [top_chunk]
        expected = Explanation(explanation="grounded answer", source_url=top_chunk.source_url)
        mock_generation_controller.explain.return_value = expected

        # when
        actual = service.explain_flag("flag-1")

        # then
        assert actual is expected
        mock_retrieval_controller.retrieve.assert_called_once_with(
            query="fui al mercado",
            top_k=RETRIEVAL_TOP_K,
            category="preterite",
        )
        # The flag handed to Generation is the one reconstructed from disk.
        mock_generation_controller.explain.assert_called_once_with(flag, top_chunk)

    def test_should_raise_flag_not_found_when_the_real_file_has_no_such_id(
        self, service, flag_broker, mock_retrieval_controller, practice_log_broker
    ):
        # given
        flag_broker.save_flags([make_flag("flag-1")])

        # when / then
        with pytest.raises(FlagNotFoundException):
            service.explain_flag("does-not-exist")
        with pytest.raises(FlagNotFoundException):
            service.record_practice("does-not-exist", "fui al mercado")

        mock_retrieval_controller.retrieve.assert_not_called()
        assert practice_log_broker.read_attempts() == []
