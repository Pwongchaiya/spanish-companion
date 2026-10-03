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
from api.brokers.transcription.transcription_broker import AzureTranscriptionBroker
from api.exposers.transcription import make_transcription_blueprint
from api.services.foundations.transcription.transcription_service import TranscriptionService
from api.brokers.ingestion_queue import SqlAlchemyIngestionQueueBroker
from api.services.foundations.ingestion_queue import IngestionQueueService
from api.services.processings.ingestion_queue import IngestionQueueProcessingService
from api.brokers.learner_profile import SqlAlchemyLearnerProfileBroker
from api.brokers.logging import StdlibLoggingBroker
from api.brokers.mistake_pattern.mistake_pattern_broker import SqlAlchemyMistakePatternBroker
from api.brokers.practice_log import JsonLinesPracticeLogBroker
from api.brokers.topic_covered import SqlAlchemyTopicCoveredBroker
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
from api.services.foundations.topic_covered import TopicCoveredService
from api.services.foundations.tts import TtsService
from api.services.orchestrations.review import ReviewOrchestrationService
from api.services.processings.learner_profile import LearnerProfileProcessingService
from api.services.processings.mistake_pattern import MistakePatternProcessingService
from api.services.processings.topic_covered import TopicCoveredProcessingService
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
                # #67: q023 ("La cuenta, por favor.") false-positived at 0.65 -- articles 0.5948,
                # object-pronouns 0.6002 both cleared the old ceiling. 0.59 drops both; every
                # real-topic eval question still hits at rank 1 (category match bypasses this filter).
                float(os.getenv("RETRIEVAL_MAX_DISTANCE", "0.59")),
                logging_broker=logging_broker,
            )
        ],
        alternate_strategy=LexicalStrategy(chunk_repository_service, logging_broker=logging_broker),
        candidate_pool=int(os.getenv("RETRIEVAL_CANDIDATE_POOL", "50")),
        logging_broker=logging_broker,
    )
    generation_service = GenerationService(
        # #86: pin the shared/draft broker too -- see api/app.py's identical wiring
        # for the full rationale (affects explain()'s draft plus every other
        # self._broker caller, all judgment/explanation calls).
        GeminiGenerationBroker(temperature=float(os.getenv("GENERATION_TEMPERATURE", "0"))),
        logging_broker=logging_broker,
        # #68: reflective grounding judge randomly rejected good drafts at the
        # default (nonzero) temperature it shared with the draft call itself.
        judge_broker=GeminiGenerationBroker(temperature=float(os.getenv("GROUNDING_JUDGE_TEMPERATURE", "0"))),
    )
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
    # F1 follow-up: only production caller of record_topic() -- same DB this
    # deployment already reads for retrieval/mistake_pattern above.
    topic_covered_processing_service = TopicCoveredProcessingService(
        TopicCoveredService(SqlAlchemyTopicCoveredBroker(database_url), logging_broker=logging_broker)
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
        ingestion_queue_processing_service=IngestionQueueProcessingService(
            IngestionQueueService(SqlAlchemyIngestionQueueBroker(database_url), logging_broker=logging_broker)
        ),
        topic_covered_processing_service=topic_covered_processing_service,
        logging_broker=logging_broker,
    )
    app.register_blueprint(make_review_blueprint(review_orchestrator))

    # --- Tts (roadmap item B6: minimal-pair listening check) -- no mic/
    # Voice Conversation dependency, safe for the public deployment ---
    tts_service = TtsService(AzureTtsBroker(), logging_broker=logging_broker)
    app.register_blueprint(make_tts_blueprint(tts_service))

    # --- Transcription -- Review's speak-to-practice uploads a browser-recorded
    # WAV; no server mic, safe for the public deployment ---
    transcription_service = TranscriptionService(AzureTranscriptionBroker(), logging_broker=logging_broker)
    app.register_blueprint(make_transcription_blueprint(transcription_service))

    @app.route("/")
    def index():
        return send_from_directory(FRONTEND_DIST, "index.html")

    return app


# Bare WSGI-importable app object -- production WSGI server (gunicorn)
# targets api.app_public:app directly, not a factory call.
app = create_public_app()


if __name__ == "__main__":
    create_public_app().run(port=5000)
