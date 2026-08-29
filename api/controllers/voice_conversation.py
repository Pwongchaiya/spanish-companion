"""Subprocess entrypoint for the live voice conversation.

    python -m api.controllers.voice_conversation

This is the exact command api/brokers/bot_process.py's BOT_COMMAND already
launches. Hand-written, no agent, per CLAUDE.md's Phase 2 Layer-Agent
Mapping — Voice Conversation is a fully manual, supervised port at every
layer.

Flask-initiated /stop is handled entirely in the Service
(ConversationOrchestrator._watch_for_stop_signal, polling BotProcessBroker's
stop-flag file) — nothing to wire up here. Ctrl+C still works interactively
via Python's default SIGINT -> KeyboardInterrupt handling.
"""

import asyncio

from dotenv import load_dotenv
from loguru import logger

from api.brokers.flag import JsonFileFlagBroker
from api.services.voice_conversation import ConversationOrchestrator


def main() -> None:
    load_dotenv()

    orchestrator = ConversationOrchestrator(JsonFileFlagBroker())
    logger.info("Voice loop starting — talk into your mic. Ctrl+C to stop.")
    asyncio.run(orchestrator.run())


if __name__ == "__main__":
    main()
