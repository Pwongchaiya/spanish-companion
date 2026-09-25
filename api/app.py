"""Flask app factory — wires every feature's Exposer into one process.

Owned by the main build session, not any single feature or layer agent
(per CLAUDE.md's Phase 2 Layer-Agent Mapping build order: "app.py
integration ... owned by the main session, no single feature/agent owns
it"). Constructs every broker/service exactly once here — the composition
root — and injects the finished objects into each feature's Blueprint
factory. Review's four service dependencies (FlagService,
PracticeLogService, HybridRetrievalOrchestrationService, GenerationService) are wired
directly into ReviewOrchestrationService -- the pass-through
RetrievalController/GenerationController this used to route through are
gone (6-layer Standard rebuild, Wave 7).

`/api/events` reads the transcript file by its own env var (not by
importing api.services.orchestrations.voice_conversation) so this process never pulls in
Voice Conversation's pipecat/Azure/Google dependencies — Voice Conversation
runs as a separate subprocess precisely to keep those out of the Flask
process (see BotProcessBroker).
"""

import json
import logging
import os
import time
from dataclasses import asdict
from pathlib import Path
from typing import FrozenSet, Optional
from urllib.parse import urlparse

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request, send_from_directory

from api.brokers.audio_storage import LocalWavAudioStorageBroker
from api.brokers.bot_process import SubprocessBotProcessBroker
from api.brokers.configuration import EnvConfigurationBroker
from api.brokers.flag import JsonFileFlagBroker
from api.brokers.learner_profile import SqlAlchemyLearnerProfileBroker
from api.brokers.logging import StdlibLoggingBroker
from api.brokers.mistake_pattern.mistake_pattern_broker import SqlAlchemyMistakePatternBroker
from api.brokers.practice_log import JsonLinesPracticeLogBroker
from api.brokers.pronunciation_assessment import AzurePronunciationAssessmentBroker
from api.brokers.pronunciation_result import SqlAlchemyPronunciationResultBroker
from api.brokers.session_audio import SqlAlchemySessionAudioBroker
from api.brokers.session_log import FileSessionLogBroker
from api.brokers.session_log_entry import SqlAlchemySessionLogEntryBroker
from api.brokers.ingestion_queue import SqlAlchemyIngestionQueueBroker
from api.brokers.topic_covered import SqlAlchemyTopicCoveredBroker
from api.brokers.transcription.transcription_broker import AzureTranscriptionBroker
from api.services.foundations.ingestion_queue import IngestionQueueService
from api.services.processings.ingestion_queue import IngestionQueueProcessingService
from api.brokers.tts import AzureTtsBroker
from api.exposers.learner_profile import LearnerProfileController
from api.exposers.progress import make_progress_blueprint
from api.exposers.pronunciation import make_pronunciation_blueprint
from api.exposers.review import make_review_blueprint
from api.exposers.session_lifecycle import make_session_lifecycle_blueprint
from api.exposers.session_replay import make_session_replay_blueprint
from api.exposers.transcription import make_transcription_blueprint
from api.exposers.tts import make_tts_blueprint
from api.services.foundations.audio_storage import AudioStorageService
from api.services.foundations.flag import FlagService
from api.services.foundations.learner_profile import LearnerProfileService
from api.services.foundations.live_transcript import LiveTranscriptService
from api.services.foundations.mistake_pattern import MistakePatternService
from api.services.foundations.practice_log import PracticeLogService
from api.services.foundations.pronunciation_assessment import PronunciationAssessmentService
from api.services.foundations.pronunciation_result import PronunciationResultService
from api.services.foundations.session_audio import SessionAudioService
from api.services.foundations.session_lifecycle import ConversationSessionService
from api.services.foundations.session_log_entry import SessionLogEntryService
from api.services.foundations.topic_covered import TopicCoveredService
from api.services.foundations.transcription.transcription_service import TranscriptionService
from api.services.foundations.tts import TtsService
from api.services.orchestrations.learner_profile import LearnerProfileOrchestrationService
from api.services.aggregations.session_recap import SessionRecapAggregationService
from api.services.orchestrations.progress import ProgressOrchestrationService
from api.services.orchestrations.pronunciation import PronunciationOrchestrationService
from api.services.orchestrations.review import ReviewOrchestrationService
from api.services.orchestrations.session_audio_recording import SessionAudioRecordingOrchestrationService
from api.services.orchestrations.session_replay import SessionReplayOrchestrationService
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

load_dotenv()
logging.basicConfig(level=logging.INFO)

REPO_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIST = REPO_ROOT / "frontend" / "dist"

# Origin/Referer CSRF-shaped check, per the architecture decision record's
# "Resolved: /start origin check" — applied app-wide (not per-blueprint)
# so /start /stop /status and /review* are covered uniformly with one
# check, confirmed over per-blueprint duplication. Flask binds
# localhost-only (no network exposure), so this mitigates a drive-by
# same-machine browser tab, not a network attacker — a request with
# neither header (same-origin fetch in some browsers, curl during manual
# testing) is allowed through; this is a lightweight mitigation, not a
# full auth system.
ALLOWED_ORIGINS: FrozenSet[str] = frozenset(
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        # Both hostname forms are needed: Flask's dev server accepts either,
        # and which one a browser sends as Origin/Referer depends on how the
        # user navigated there (typed "localhost" vs "127.0.0.1", or a link
        # using one or the other) — missing either form 403s real requests.
        "http://localhost:5000,http://localhost:5173,http://127.0.0.1:5000,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
)

# Same path/env-vars as api/brokers/session_log/session_log_broker.py's
# DEFAULT_TRANSCRIPT_FILE_PATH / DEFAULT_TURN_STATE_FILE_PATH
# — duplicated as constants, not imported, to keep pipecat/Azure/Google out of
# this process (see module docstring).
TRANSCRIPT_FILE_PATH = Path(os.getenv("TRANSCRIPT_FILE_PATH", str(REPO_ROOT / "data" / "live_transcript.jsonl")))
TURN_STATE_FILE_PATH = Path(os.getenv("TURN_STATE_FILE_PATH", str(REPO_ROOT / "data" / "turn_state.txt")))
SSE_POLL_INTERVAL_SECONDS = float(os.getenv("SSE_POLL_INTERVAL_SECONDS", "1"))

# Cap on any request body -- sized for POST /pronunciation/assess's WAV upload
# (the Foundation service itself rejects WAVs over 1 MiB with a 400, so 2 MiB
# leaves room for multipart framing).
MAX_UPLOAD_BYTES = 2 * 1024 * 1024


def _register_upload_limit(app: Flask) -> None:
    """Cap request bodies and answer an oversize one with JSON, not Flask's HTML 413 page."""
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES

    @app.errorhandler(413)
    def request_too_large(_error):
        return jsonify({"error": f"request body exceeds {MAX_UPLOAD_BYTES} bytes"}), 413


def _read_transcript() -> list:
    if not TRANSCRIPT_FILE_PATH.exists():
        return []
    turns = []
    for line in TRANSCRIPT_FILE_PATH.read_text(encoding="utf-8").splitlines():
        try:
            turns.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return turns


def _read_turn_state() -> Optional[str]:
    if not TURN_STATE_FILE_PATH.exists():
        return None
    return TURN_STATE_FILE_PATH.read_text(encoding="utf-8").strip() or None


def _is_allowed_origin(header: str, allowed_origins: FrozenSet[str]) -> bool:
    # Exact match on scheme+host, not startswith() — a prefix match let
    # "http://localhost:5000.evil.com" pass by starting with the allowed
    # "http://localhost:5000".
    parsed = urlparse(header)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    return origin in allowed_origins


def create_app() -> Flask:
    app = Flask(__name__, static_folder=str(FRONTEND_DIST), static_url_path="")
    _register_upload_limit(app)

    @app.before_request
    def check_origin() -> Optional[tuple]:
        header = request.headers.get("Origin") or request.headers.get("Referer")
        if header is None:
            return None
        if not _is_allowed_origin(header, ALLOWED_ORIGINS):
            return jsonify({"error": "origin not allowed"}), 403
        return None

    # One LoggingBroker shared by every service in the process — each
    # service already defaulted to a StdlibLoggingBroker over the same
    # named logger; constructing it once here makes that sharing explicit
    # at the composition root instead of implicit in each default arg.
    logging_broker = StdlibLoggingBroker()

    # One ConfigurationBroker likewise, for the same reason: services read
    # their knobs through this seam now instead of calling os.getenv at
    # import time, which is what made config impossible to vary per test
    # (audit finding H1).
    configuration_broker = EnvConfigurationBroker()

    # flag_service is built here (ahead of Session Lifecycle and Review, both
    # of which need it) rather than duplicated — LearnerProfile's
    # scenario-suggestion orchestrator and Review's orchestrator share this
    # one FlagService/JsonFileFlagBroker instance.
    flag_service = FlagService(JsonFileFlagBroker(), logging_broker=logging_broker)

    # --- LearnerProfile (Phase 3: session-scenario suggestion, see
    # decisions/dynamic-bot-behavior-and-learner-memory.md) ---
    database_url = os.environ["DATABASE_URL"]
    learner_profile_service = LearnerProfileService(
        SqlAlchemyLearnerProfileBroker(database_url), logging_broker=logging_broker
    )
    mistake_pattern_service = MistakePatternService(
        SqlAlchemyMistakePatternBroker(database_url), logging_broker=logging_broker
    )
    topic_covered_service = TopicCoveredService(
        SqlAlchemyTopicCoveredBroker(database_url), logging_broker=logging_broker
    )
    # Roadmap C1/C3 -- the only new broker Progress needed; A5/F1
    # reuse the services already built above.
    session_log_entry_service = SessionLogEntryService(
        SqlAlchemySessionLogEntryBroker(database_url), logging_broker=logging_broker
    )
    # Shared with Review below (LearnerProfile Phase 2) -- both stateless,
    # one instance each is enough.
    learner_profile_processing_service = LearnerProfileProcessingService(learner_profile_service)
    mistake_pattern_processing_service = MistakePatternProcessingService(mistake_pattern_service)
    # F1 follow-up: shared with Review below (only production caller of
    # record_topic() -- see topic_covered_processing_service.py docstring).
    topic_covered_processing_service = TopicCoveredProcessingService(topic_covered_service)
    learner_profile_orchestrator = LearnerProfileOrchestrationService(
        learner_profile_processing_service,
        mistake_pattern_service,
        topic_covered_service,
        flag_service,
        logging_broker=logging_broker,
        mistake_pattern_processing_service=mistake_pattern_processing_service,
        configuration_broker=configuration_broker,
    )
    learner_profile_controller = LearnerProfileController(learner_profile_orchestrator)

    # --- Session Lifecycle ---
    session_service = ConversationSessionService(
        SubprocessBotProcessBroker(),
        logging_broker=logging_broker,
        configuration_broker=configuration_broker,
    )
    app.register_blueprint(make_session_lifecycle_blueprint(session_service, learner_profile_controller))

    # --- Review (composes Retrieval + Generation via rag's Foundation/
    # Orchestration services directly -- RetrievalController/
    # GenerationController were pure pass-throughs and are gone) ---
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
                float(configuration_broker.get("RETRIEVAL_MAX_DISTANCE", "0.65")),
                logging_broker=logging_broker,
            )
        ],
        alternate_strategy=LexicalStrategy(chunk_repository_service, logging_broker=logging_broker),
        logging_broker=logging_broker,
    )
    generation_service = GenerationService(GeminiGenerationBroker(), logging_broker=logging_broker)
    practice_log_service = PracticeLogService(JsonLinesPracticeLogBroker(), logging_broker=logging_broker)
    review_orchestrator = ReviewOrchestrationService(
        flag_service=flag_service,
        practice_log_service=practice_log_service,
        retrieval_service=retrieval_service,
        generation_service=generation_service,
        learner_profile_processing_service=learner_profile_processing_service,
        mistake_pattern_processing_service=mistake_pattern_processing_service,
        session_log_entry_service=session_log_entry_service,
        live_transcript_service=LiveTranscriptService(FileSessionLogBroker(), logging_broker=logging_broker),
        ingestion_queue_processing_service=IngestionQueueProcessingService(
            IngestionQueueService(SqlAlchemyIngestionQueueBroker(database_url), logging_broker=logging_broker)
        ),
        topic_covered_processing_service=topic_covered_processing_service,
        logging_broker=logging_broker,
        configuration_broker=configuration_broker,
    )
    app.register_blueprint(make_review_blueprint(review_orchestrator))

    # --- Session replay (roadmap E3) -- listen back to a recorded session with
    # its flags on a timeline. Separate blueprint/orchestrator from Review
    # (additive; Review's own service is untouched). Retention: recordings
    # older than AUDIO_RETENTION_DAYS (default 30) are pruned once, here at
    # startup -- best-effort, a DB/disk hiccup must not stop the app booting. ---
    session_audio_service = SessionAudioService(
        SqlAlchemySessionAudioBroker(database_url), logging_broker=logging_broker
    )
    app.register_blueprint(
        make_session_replay_blueprint(
            SessionReplayOrchestrationService(
                session_audio_service, flag_service, session_log_entry_service, logging_broker=logging_broker
            )
        )
    )
    try:
        removed = SessionAudioRecordingOrchestrationService(
            AudioStorageService(LocalWavAudioStorageBroker(), logging_broker=logging_broker),
            session_audio_service,
            logging_broker=logging_broker,
        ).prune_expired(int(configuration_broker.get("AUDIO_RETENTION_DAYS", "30")))
        if removed:
            logging_broker.log_info("Pruned %s expired session recording(s)", removed)
    except Exception as e:  # noqa: BLE001 -- startup pruning is best-effort
        logging_broker.log_warning("Session audio pruning skipped: %s", e)

    # --- Progress (roadmap Phase 2: A5 cumulative mistake dashboard, F1
    # corpus coverage map) -- read-only, no new brokers; reuses the
    # mistake_pattern_service/topic_covered_service/
    # learner_profile_processing_service instances already built above ---
    pronunciation_result_service = PronunciationResultService(
        SqlAlchemyPronunciationResultBroker(database_url), logging_broker=logging_broker
    )
    progress_orchestrator = ProgressOrchestrationService(
        learner_profile_processing_service,
        mistake_pattern_service,
        topic_covered_service,
        session_log_entry_service,
        pronunciation_result_service,
        logging_broker=logging_broker,
        configuration_broker=configuration_broker,
    )
    # --- Session recap (roadmap C2) -- Aggregation layer, composing
    # Review's flag list with Progress's latest-completed-session read for
    # the one Exposer route (GET /progress/recap) that needs both. Reuses
    # the review_orchestrator/progress_orchestrator instances already built
    # above -- no new brokers, no new Foundation/Processing services. ---
    tts_service = TtsService(AzureTtsBroker(), logging_broker=logging_broker)
    session_recap_aggregator = SessionRecapAggregationService(
        review_orchestrator,
        progress_orchestrator,
        tts_service,
        logging_broker=logging_broker,
    )
    app.register_blueprint(make_progress_blueprint(progress_orchestrator, session_recap_aggregator))

    # --- Tts (roadmap item B6: minimal-pair listening check) -- stateless
    # single-call feature, no Orchestration layer needed ---
    app.register_blueprint(make_tts_blueprint(tts_service))

    # --- Pronunciation (roadmap Phase 4) -- Azure scoring + persistence, composed by one
    # Orchestration service; the result service is shared with Progress's trend read above ---
    pronunciation_assessment_service = PronunciationAssessmentService(
        AzurePronunciationAssessmentBroker(), logging_broker=logging_broker
    )
    pronunciation_orchestrator = PronunciationOrchestrationService(
        pronunciation_assessment_service,
        pronunciation_result_service,
        logging_broker=logging_broker,
    )
    app.register_blueprint(make_pronunciation_blueprint(pronunciation_orchestrator))

    # --- Transcription (review-three-pane HANDOFF.md section 4) -- free-form WAV -> text
    # for the spoken-practice path; unbiased recognition, no reference text (unlike
    # Pronunciation above), single broker, no Orchestration layer needed ---
    transcription_service = TranscriptionService(AzureTranscriptionBroker(), logging_broker=logging_broker)
    app.register_blueprint(make_transcription_blueprint(transcription_service))

    # --- /api/events SSE — status/transcript/flags/turn_state, per the
    # architecture decision record's "Resolved: /api/events SSE event
    # schema" (turn_state added post-Wave-8, see
    # decisions/tri-nature-gate-design.md's follow-up 2). status/turn_state
    # are pushed only on change (frontend gets the initial status via
    # /status; turn_state has no such initial-fetch endpoint, so it starts
    # None until the voice subprocess writes its first transition);
    # transcript/flags each carry their full current list on every push
    # they do occur on, matching how the source files themselves are read
    # (whole file, not appended deltas).
    @app.route("/api/events")
    def events():
        def stream():
            last_status = last_transcript = last_flags = last_turn_state = None
            while True:
                status = asdict(session_service.get_status())
                if status != last_status:
                    yield f"data: {json.dumps({'type': 'status', 'status': status})}\n\n"
                    last_status = status

                transcript = _read_transcript()
                if transcript != last_transcript:
                    yield f"data: {json.dumps({'type': 'transcript', 'turns': transcript})}\n\n"
                    last_transcript = transcript

                turn_state = _read_turn_state()
                if turn_state != last_turn_state:
                    yield f"data: {json.dumps({'type': 'turn_state', 'state': turn_state})}\n\n"
                    last_turn_state = turn_state

                flags = [
                    asdict(flag) | {"timestamp": flag.timestamp.isoformat()}
                    for flag in flag_service.list_flags()
                ]
                if flags != last_flags:
                    yield f"data: {json.dumps({'type': 'flags', 'flags': flags})}\n\n"
                    last_flags = flags

                time.sleep(SSE_POLL_INTERVAL_SECONDS)

        return Response(stream(), mimetype="text/event-stream", headers={"Cache-Control": "no-cache"})

    @app.route("/")
    def index():
        return send_from_directory(FRONTEND_DIST, "index.html")

    return app


if __name__ == "__main__":
    create_app().run(port=5000)
