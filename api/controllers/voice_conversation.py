"""Subprocess entrypoint for the live voice conversation.

    python -m api.controllers.voice_conversation

This is the exact command api/brokers/bot_process.py's BOT_COMMAND already
launches. Hand-written, no agent, per CLAUDE.md's Phase 2 Layer-Agent
Mapping — Voice Conversation is a fully manual, supervised port at every
layer.

Windows SIGBREAK handling lives here (not in the Service): a subprocess-
lifecycle concern, not conversation logic — BotProcessBroker's
send_graceful_signal() sends CTRL_BREAK_EVENT, and this converts it to
KeyboardInterrupt so ConversationOrchestrator.run()'s try/finally (flag +
transcript persistence) actually executes on a Flask-initiated /stop,
the same path Ctrl+C already takes interactively.
"""

import asyncio
import signal

from dotenv import load_dotenv
from loguru import logger

from api.brokers.flag import JsonFileFlagBroker
from api.services.voice_conversation import ConversationOrchestrator


def main() -> None:
    load_dotenv()

    # Windows has no default handler for CTRL_BREAK_EVENT (SIGBREAK) — unlike
    # SIGINT/Ctrl+C, which Python auto-converts to KeyboardInterrupt, an
    # unhandled SIGBREAK just kills the process outright, skipping
    # ConversationOrchestrator.run()'s try/finally entirely (verified in
    # Phase 1: session log/flags never got written). This lets
    # BotProcessBroker.send_graceful_signal() (called from Flask's /stop
    # route via ConversationSessionService) request the same graceful
    # shutdown Ctrl+C already gets interactively.
    if hasattr(signal, "SIGBREAK"):

        def _handle_sigbreak(signum, frame) -> None:
            raise KeyboardInterrupt

        signal.signal(signal.SIGBREAK, _handle_sigbreak)

    orchestrator = ConversationOrchestrator(JsonFileFlagBroker())
    logger.info("Voice loop starting — talk into your mic. Ctrl+C to stop.")
    asyncio.run(orchestrator.run())


if __name__ == "__main__":
    main()
