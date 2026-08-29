"""Flask app factory — wires every feature's Controller into one process.

Owned by the main build session, not any single feature or layer agent
(per CLAUDE.md's Phase 2 Layer-Agent Mapping build order: "app.py
integration ... owned by the main session, no single feature/agent owns
it"). Constructs every broker/service/controller exactly once here — the
composition root — and injects the finished objects into each feature's
Blueprint factory.

Partial build: `/api/events` SSE is not implemented yet. It depends on
Voice Conversation's transcript/flag file contract, which hasn't been
built (Voice Conversation is a fully manual, supervised port — see
CLAUDE.md). Everything else below is independent of Voice Conversation
and is wired now so Session Lifecycle and Review are actually runnable.
"""

import os
from pathlib import Path
from typing import Optional, Tuple

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

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
    review_orchestrator = ReviewOrchestrator(
        flag_broker=JsonFileFlagBroker(),
        practice_log_broker=JsonLinesPracticeLogBroker(),
        retrieval_controller=retrieval_controller,
        generation_controller=generation_controller,
    )
    app.register_blueprint(make_review_blueprint(review_orchestrator))

    # TODO(voice-conversation): /api/events SSE — needs Voice Conversation's
    # transcript/flag file contract settled first. Push three event types
    # (status, transcript, flags) per the architecture decision record's
    # "Resolved: /api/events SSE event schema".

    @app.route("/")
    def index():
        return send_from_directory(FRONTEND_DIST, "index.html")

    return app


if __name__ == "__main__":
    create_app().run(port=5000)
