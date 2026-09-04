# Multi-stage build for the "J5" public deployment (api/app_public.py).
#
# Render's native runtimes are single-language (see render.com/docs/native-runtimes) --
# there's no supported way to get both Node (frontend build) and Python
# (gunicorn runtime) into one native-runtime service. Docker is Render's
# documented path for this ("Render supports parallelized multi-stage
# builds" -- render.com/docs/docker), so: stage 1 builds frontend/dist with
# npm, stage 2 is the Python runtime that serves it. Render passes the port
# to bind via the $PORT env var (default 10000 if unset -- render.com/docs/web-services).

# --- Stage 1: frontend (Review UI only, no Voice Conversation tab) ---
FROM node:22-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build:public

# --- Stage 2: Python runtime ---
FROM python:3.12-slim AS runtime
WORKDIR /app

# pipecat-ai[local,google] pulls in pyaudio, which has no prebuilt Linux
# wheel and compiles a C extension against portaudio -- needed at pip-install
# time even though app_public.py never imports Voice Conversation at runtime
# (requirements.txt is shared with the full app, and this file is only
# adding gunicorn to it, not trimming it).
# libc6-dev is a "Recommended" package of gcc, not a hard dependency --
# --no-install-recommends drops it, which leaves gcc unable to find
# stdlib.h. Pinned explicitly rather than dropping --no-install-recommends
# wholesale.
RUN apt-get update && apt-get install -y --no-install-recommends -o Acquire::Retries=5 \
        gcc libc6-dev portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ api/
COPY rag/ rag/
COPY alembic/ alembic/
COPY alembic.ini .
COPY data/demo_flags.json data/demo_flags.json
COPY --from=frontend-build /app/frontend/dist frontend/dist

ENV PYTHONUNBUFFERED=1
# Local `docker run` fallback only -- Render always injects its own $PORT.
ENV PORT=10000
EXPOSE 10000

# ponytail: single worker -- SentenceTransformerEmbeddingModelBroker loads a
# ~470MB embedding model per worker process, and Render's small instance
# tiers don't have room for two copies. Raise --workers only alongside a
# bigger instance. --timeout 120 because /review/flags/<id>/explain makes a
# real Gemini call that can outrun gunicorn's 30s default.
CMD gunicorn api.app_public:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120
