"""Unit test for api.app_public's route registration.

Doesn't call create_public_app() against live infra -- same reasoning as
tests/acceptance/apis/session_lifecycle/test_start_stop_status.py's docstring
(no injection point for the real brokers) and tests/unit/test_app_origin_check.py
(avoid the heavy composition root). Every broker constructor create_public_app()
touches is patched out so this stays a fast unit test with no DB/model/LLM
dependency; DATABASE_URL is faked since ChunkRepositoryService reads it from
os.environ directly.

The point of this test: confirm the public app registers Review's routes and
NOTHING from Session Lifecycle or /api/events -- that boundary is the whole
reason api/app_public.py exists (see its module docstring).
"""

from unittest.mock import patch

import pytest


@pytest.fixture
def public_app(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake/fake")
    # Patched at each broker's own defining module, not api.app_public's --
    # api.app_public's `app = create_public_app()` runs at import time (it's
    # the bare WSGI-importable object the brief requires), so if this is the
    # first import of api.app_public in the process, patching its own
    # namespace would be too late: the module-level call already ran against
    # the real, unpatched constructors before patch() could reach in. Patching
    # the source modules instead means api.app_public's `from X import Y`
    # picks up the mock regardless of import order.
    with (
        patch("rag.brokers.chunk_repository.SqlAlchemyChunkRepositoryBroker"),
        patch("rag.brokers.embedding_model.SentenceTransformerEmbeddingModelBroker"),
        patch("rag.brokers.generation.GeminiGenerationBroker"),
        patch("api.brokers.flag.JsonFileFlagBroker"),
        patch("api.brokers.practice_log.JsonLinesPracticeLogBroker"),
    ):
        from api.app_public import create_public_app

        yield create_public_app()


class TestAppPublicRoutes:

    def test_should_register_review_routes_and_index_only(self, public_app):
        rules = {rule.rule for rule in public_app.url_map.iter_rules()}

        assert "/review/flags" in rules
        assert "/review/flags/<flag_id>/explain" in rules
        assert "/review/flags/<flag_id>/practice" in rules
        assert "/" in rules

    def test_should_not_register_session_lifecycle_or_sse_routes(self, public_app):
        rules = {rule.rule for rule in public_app.url_map.iter_rules()}

        assert "/start" not in rules
        assert "/stop" not in rules
        assert "/status" not in rules
        assert "/api/events" not in rules
