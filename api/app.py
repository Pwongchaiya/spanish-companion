"""Flask app factory — wires every feature's Controller into one process.

Owned by the main build session, not any single feature or layer agent
(per CLAUDE.md's Phase 2 Layer-Agent Mapping build order: "app.py
integration ... owned by the main session, no single feature/agent owns
it"). Constructs every broker/service/controller exactly once here — the
composition root — and injects the finished objects into each feature's
Blueprint factory.

`/api/events` reads the transcript file by its own env var (not by
importing api.services.voice_conversation) so this process never pulls in
Voice Conversation's pipecat/Azure/Google dependencies — Voice Conversation
runs as a separate subprocess precisely to keep those out of the Flask
process (see BotProcessBroker).
"""

import json
import os
import time
from dataclasses import asdict
from pathlib import Path
from typing import Optional, Tuple

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request, send_from_directory

from api.brokers.bot_process import SubprocessBotProcessBroker
from api.brokers.flag import JsonFileFlagBroker
from api.brokers.practice_log import JsonLinesPracticeLogBroker
from api.controllers.review import make_review_blueprint
from api.controllers.session_lifecycle import make_session_lifecycle_blueprint
from api.services.review import ReviewOrchestrator
from api.services.session_lifecycle import ConversationSessionService
from rag.brokers.chunk_repository import SqlAlchemyChunkRepositoryBroker
from rag.brokers.embedding_model import SentenceTransformerEmbeddingModelBroker
from rag.brokers.generation import GeminiGenerationBroker
from rag.controllers.generation import GenerationController
from rag.controllers.retrieval import RetrievalController
from rag.services.generation import GenerationService
from rag.services.retrieval.service import HybridRetrievalService

load_dotenv()

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
ALLOWED_ORIGINS: Tuple[str, ...] = tuple(
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

# Same path/env-var as api/services/voice_conversation.py's TRANSCRIPT_FILE_PATH
# — duplicated as a constant, not imported, to keep pipecat/Azure/Google out of
# this process (see module docstring).
TRANSCRIPT_FILE_PATH = Path(os.getenv("TRANSCRIPT_FILE_PATH", str(REPO_ROOT / "data" / "live_transcript.jsonl")))
SSE_POLL_INTERVAL_SECONDS = float(os.getenv("SSE_POLL_INTERVAL_SECONDS", "1"))


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


def create_app() -> Flask:
    app = Flask(__name__, static_folder=str(FRONTEND_DIST), static_url_path="")

    @app.before_request
    def check_origin() -> Optional[Tuple[object, int]]:
        header = request.headers.get("Origin") or request.headers.get("Referer")
        if header is None:
            return None
        if not header.startswith(ALLOWED_ORIGINS):
            return jsonify({"error": "origin not allowed"}), 403
        return None

    # --- Session Lifecycle ---
    session_service = ConversationSessionService(SubprocessBotProcessBroker())
    app.register_blueprint(make_session_lifecycle_blueprint(session_service))

    # --- Review (composes Retrieval + Generation via rag's controllers) ---
    chunk_repository = SqlAlchemyChunkRepositoryBroker(connection_string=os.environ["DATABASE_URL"])
    embedding_model = SentenceTransformerEmbeddingModelBroker()
    retrieval_controller = RetrievalController(HybridRetrievalService(embedding_model, chunk_repository))
    generation_controller = GenerationController(GenerationService(GeminiGenerationBroker()))
    flag_broker = JsonFileFlagBroker()
    review_orchestrator = ReviewOrchestrator(
        flag_broker=flag_broker,
        practice_log_broker=JsonLinesPracticeLogBroker(),
        retrieval_controller=retrieval_controller,
        generation_controller=generation_controller,
    )
    app.register_blueprint(make_review_blueprint(review_orchestrator))

    # --- /api/events SSE — status/transcript/flags, per the architecture
    # decision record's "Resolved: /api/events SSE event schema". status is
    # pushed only on change (frontend gets the initial value via /status);
    # transcript/flags each carry their full current list on every push they
    # do occur on, matching how the source files themselves are read (whole
    # file, not appended deltas).
    @app.route("/api/events")
    def events():
        def stream():
            last_status = last_transcript = last_flags = None
            while True:
                status = asdict(session_service.get_status())
                if status != last_status:
                    yield f"data: {json.dumps({'type': 'status', 'status': status})}\n\n"
                    last_status = status

                transcript = _read_transcript()
                if transcript != last_transcript:
                    yield f"data: {json.dumps({'type': 'transcript', 'turns': transcript})}\n\n"
                    last_transcript = transcript

                flags = [
                    asdict(flag) | {"timestamp": flag.timestamp.isoformat()}
                    for flag in flag_broker.load_flags()
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
