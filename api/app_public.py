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
from api.brokers.learner_profile import SqlAlchemyLearnerProfileBroker
from api.brokers.logging import StdlibLoggingBroker
from api.brokers.mistake_pattern.mistake_pattern_broker import SqlAlchemyMistakePatternBroker
from api.brokers.practice_log import JsonLinesPracticeLogBroker
from api.brokers.session_log import FileSessionLogBroker
from api.brokers.session_log_entry import SqlAlchemySessionLogEntryBroker
from api.brokers.tts import AzureTtsBroker
from api.exposers.review import make_review_blueprint
from api.exposers.tts import make_tts_blueprint
from api.services.foundations.flag import FlagService
from api.services.foundations.learner_profile import LearnerProfileService
from api.services.foundations.live_transcript import LiveTranscriptService
from api.services.foundations.mistake_pattern import MistakePatternService
from api.services.foundations.practice_log import PracticeLogService
from api.services.foundations.session_log_entry import SessionLogEntryService
from api.services.foundations.tts import TtsService
from api.services.orchestrations.review import ReviewOrchestrationService
from api.services.processings.learner_profile import LearnerProfileProcessingService
from api.services.processings.mistake_pattern import MistakePatternProcessingService
from rag.brokers.chunk_repository import SqlAlchemyChunkRepositoryBroker
from rag.brokers.embedding_model import SentenceTransformerEmbeddingModelBroker
from rag.brokers.generation import GeminiGenerationBroker
from rag.services.foundations.chunk_repository import ChunkRepositoryService
from rag.services.foundations.embedding_model import EmbeddingModelService
from rag.services.foundations.generation import GenerationService
from rag.services.orchestrations.retrieval import HybridRetrievalOrchestrationService
from rag.services.orchestrations.retrieval.strategies.dense import DenseVectorStrategy
from rag.services.orchestrations.retrieval.strategies.lexical import LexicalStrategy
from rag.services.orchestrations.retrieval.strategies.filters import MaxDistanceFilter
from rag.services.orchestrations.retrieval.strategies.fusion import PassThroughRankFusion


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
    database_url = os.environ["DATABASE_URL"]
    chunk_repository_service = ChunkRepositoryService(
        SqlAlchemyChunkRepositoryBroker(connection_string=database_url),
        logging_broker=logging_broker,
    )
    embedding_model_service = EmbeddingModelService(
        SentenceTransformerEmbeddingModelBroker(),
        logging_broker=logging_broker,
    )
    retrieval_service = HybridRetrievalOrchestrationService(
        embedding_model_service,
        strategies=[DenseVectorStrategy(chunk_repository_service, logging_broker=logging_broker)],
        fusion=PassThroughRankFusion(logging_broker=logging_broker),
        filters=[
            MaxDistanceFilter(
                float(os.getenv("RETRIEVAL_MAX_DISTANCE", "0.65")),
                logging_broker=logging_broker,
            )
        ],
        alternate_strategy=LexicalStrategy(chunk_repository_service, logging_broker=logging_broker),
        logging_broker=logging_broker,
    )
    generation_service = GenerationService(GeminiGenerationBroker(), logging_broker=logging_broker)
    flag_service = FlagService(JsonFileFlagBroker(), logging_broker=logging_broker)
    practice_log_service = PracticeLogService(JsonLinesPracticeLogBroker(), logging_broker=logging_broker)

    # LearnerProfile Phase 2: record_practice() judges the attempt and writes
    # mistake_pattern -- same DB this deployment already reads for retrieval.
    learner_profile_processing_service = LearnerProfileProcessingService(
        LearnerProfileService(SqlAlchemyLearnerProfileBroker(database_url), logging_broker=logging_broker)
    )
    mistake_pattern_processing_service = MistakePatternProcessingService(
        MistakePatternService(SqlAlchemyMistakePatternBroker(database_url), logging_broker=logging_broker)
    )
    review_orchestrator = ReviewOrchestrationService(
        flag_service=flag_service,
        practice_log_service=practice_log_service,
        retrieval_service=retrieval_service,
        generation_service=generation_service,
        learner_profile_processing_service=learner_profile_processing_service,
        mistake_pattern_processing_service=mistake_pattern_processing_service,
        session_log_entry_service=SessionLogEntryService(
            SqlAlchemySessionLogEntryBroker(database_url), logging_broker=logging_broker
        ),
        live_transcript_service=LiveTranscriptService(FileSessionLogBroker(), logging_broker=logging_broker),
        logging_broker=logging_broker,
    )
    app.register_blueprint(make_review_blueprint(review_orchestrator))

    # --- Tts (roadmap item B6: minimal-pair listening check) -- no mic/
    # Voice Conversation dependency, safe for the public deployment ---
    tts_service = TtsService(AzureTtsBroker(), logging_broker=logging_broker)
    app.register_blueprint(make_tts_blueprint(tts_service))

    @app.route("/")
    def index():
        return send_from_directory(FRONTEND_DIST, "index.html")

    return app


# Bare WSGI-importable app object -- production WSGI server (gunicorn)
# targets api.app_public:app directly, not a factory call.
app = create_public_app()


if __name__ == "__main__":
    create_public_app().run(port=5000)
