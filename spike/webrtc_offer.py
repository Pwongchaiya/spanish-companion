"""Standalone WebRTC signaling spike -- de-risks two unknowns before any
Broker/Orchestration/Exposer rebuild: does aiortc build/import cleanly in
the deploy environment, and does the deploy host's networking pass the
ICE/UDP traffic an external browser needs. See
Projects/spanish-companion/decisions/voice-conversation-browser-webrtc-transport.md
(recommended build order, step 1).

Hand-written, not routed through a layer agent -- CLAUDE.md's Voice
Conversation waiver ("no agent, any layer") covers this: hardware/network
verification an agent can't run. Deliberately outside api/app.py's Flask
composition root for now: pipecat's SmallWebRTCRequestHandler.handle_web_request
is async, and the aiortc PeerConnection it returns must keep running on a
live event loop after the HTTP response is sent (ICE negotiation continues
in the background) -- Flask's sync WSGI workers have no persistent loop to
hand it to. A real integration needs the background-event-loop-thread design
the decision doc already flags (line ~78); this spike sidesteps that by
being its own tiny asyncio app, standalone.

Run: python spike/webrtc_offer.py, then open http://localhost:7860/ in a
browser on a DIFFERENT machine/network before trusting a "yes" on the ICE
question -- localhost-to-localhost never exercises real NAT traversal.

Pipeline is an echo (mic in -> speaker out, no STT/LLM/TTS) -- correctness
of the audio path is the only thing being tested here, not conversation
logic (that's Voice Conversation's existing pipeline, untouched).
"""

import asyncio
import os
from pathlib import Path

from aiohttp import web
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker
from pipecat.transports.base_transport import TransportParams
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
from pipecat.transports.smallwebrtc.request_handler import (
    ConnectionMode,
    SmallWebRTCRequest,
    SmallWebRTCRequestHandler,
)
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport
from pipecat.workers.runner import WorkerRunner

STATIC_DIR = Path(__file__).parent / "static"

# SINGLE: this is a spike, one tester at a time is enough to answer the
# ICE/UDP question. MULTIPLE is what a real deployment would need.
request_handler = SmallWebRTCRequestHandler(connection_mode=ConnectionMode.SINGLE)


async def run_echo_pipeline(connection: SmallWebRTCConnection) -> None:
    transport = SmallWebRTCTransport(
        webrtc_connection=connection,
        params=TransportParams(audio_in_enabled=True, audio_out_enabled=True),
    )
    pipeline = Pipeline([transport.input(), transport.output()])
    worker = PipelineWorker(pipeline, params=PipelineParams(), setup_timeout_secs=60.0)
    runner = WorkerRunner()
    await runner.add_workers(worker)
    await runner.run()


async def offer(request: web.Request) -> web.Response:
    body = await request.json()
    sdp_request = SmallWebRTCRequest.from_dict(body)

    async def on_connection(connection: SmallWebRTCConnection) -> None:
        asyncio.create_task(run_echo_pipeline(connection))

    answer = await request_handler.handle_web_request(sdp_request, on_connection)
    return web.json_response(answer)


async def index(_request: web.Request) -> web.FileResponse:
    return web.FileResponse(STATIC_DIR / "index.html")


def build_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_post("/offer", offer)
    return app


if __name__ == "__main__":
    # Render (and most PaaS hosts) inject the port to bind via $PORT --
    # a hardcoded port would 502 behind their proxy.
    web.run_app(build_app(), host="0.0.0.0", port=int(os.environ.get("PORT", 7860)))
