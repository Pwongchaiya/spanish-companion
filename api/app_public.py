"""Flask app factory for the scoped-down public deployment ("J5").

Stripped sibling of api/app.py's create_app(): exposes only Review Mode +
RAG endpoints (read-only, over a seeded demo corpus) for a hackathon public
deployment. Never registers Session Lifecycle or /api/events -- both require
Voice Conversation (SubprocessBotProcessBroker -> pipecat/Azure), which needs
local mic access and can't run on a server. This module must never import
anything from api.services.orchestrations.voice_conversation.

Reuses api.app's origin check and path constants rather than reimplementing
them -- see api/app.py's module docstring and ALLOWED_ORIGINS/
_is_allowed_origin for the prefix-match bypass fix this picks up for free.
"""

import os
from typing import Optional

from flask import Flask, jsonify, request, send_from_directory

from api.app import ALLOWED_ORIGINS, FRONTEND_DIST, _is_allowed_origin
from api.brokers.flag import JsonFileFlagBroker
from api.brokers.logging import StdlibLoggingBroker
from api.brokers.practice_log import JsonLinesPracticeLogBroker
from api.exposers.review import make_review_blueprint
from api.services.foundations.flag import FlagService
from api.services.foundations.practice_log import PracticeLogService
from api.services.orchestrations.review import ReviewOrchestrator
from rag.brokers.chunk_repository import SqlAlchemyChunkRepositoryBroker
from rag.brokers.embedding_model import SentenceTransformerEmbeddingModelBroker
from rag.brokers.generation import GeminiGenerationBroker
from rag.services.foundations.chunk_repository import ChunkRepositoryService
from rag.services.foundations.embedding_model import EmbeddingModelService
from rag.services.foundations.generation import GenerationService
from rag.services.orchestrations.retrieval import HybridRetrievalService


def create_public_app() -> Flask:
    app = Flask(__name__, static_folder=str(FRONTEND_DIST), static_url_path="")

    @app.before_request
    def check_origin() -> Optional[tuple]:
        header = request.headers.get("Origin") or request.headers.get("Referer")
        if header is None:
            return None
        if not _is_allowed_origin(header, ALLOWED_ORIGINS):
            return jsonify({"error": "origin not allowed"}), 403
        return None

    logging_broker = StdlibLoggingBroker()

    # --- Review (same dependency graph as create_app(), minus Session
    # Lifecycle / /api/events) ---
    chunk_repository_service = ChunkRepositoryService(
        SqlAlchemyChunkRepositoryBroker(connection_string=os.environ["DATABASE_URL"]),
        logging_broker=logging_broker,
    )
    embedding_model_service = EmbeddingModelService(
        SentenceTransformerEmbeddingModelBroker(),
        logging_broker=logging_broker,
    )
    retrieval_service = HybridRetrievalService(
        embedding_model_service, chunk_repository_service, logging_broker=logging_broker
    )
    generation_service = GenerationService(GeminiGenerationBroker(), logging_broker=logging_broker)
    flag_service = FlagService(JsonFileFlagBroker(), logging_broker=logging_broker)
    practice_log_service = PracticeLogService(JsonLinesPracticeLogBroker(), logging_broker=logging_broker)
    review_orchestrator = ReviewOrchestrator(
        flag_service=flag_service,
        practice_log_service=practice_log_service,
        retrieval_service=retrieval_service,
        generation_service=generation_service,
        logging_broker=logging_broker,
    )
    app.register_blueprint(make_review_blueprint(review_orchestrator))

    @app.route("/")
    def index():
        return send_from_directory(FRONTEND_DIST, "index.html")

    return app


# Bare WSGI-importable app object -- production WSGI server (gunicorn)
# targets api.app_public:app directly, not a factory call.
app = create_public_app()


if __name__ == "__main__":
    create_public_app().run(port=5000)
