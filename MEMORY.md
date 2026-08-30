# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-08-29-2126.md — Planned (not yet
built) Voice Conversation's internal Broker/Service split:
voice_conversation_service.py (513 lines, mixed responsibilities) is being
broken up to match this project's real Broker convention — every existing
Broker (FlagBroker, LoggingBroker, BotProcessBroker) is a typing.Protocol
interface + concrete impl in its own per-feature subfolder, confirmed by
reading them directly. Landed on: 3 new Brokers (ISttBroker+AzureSttBroker,
ISessionLogBroker+TextFileSessionLogBroker, IPromptBroker+TextFilePromptBroker)
under api/brokers/voice_conversation/; ConversationOrchestrator becomes
constructor-injected with all 4 Brokers (incl. the existing FlagBroker);
pipeline_builder.py/flags.py/mic_gate.py stay plain modules (no
Broker/Service ceremony — pure logic, single caller each). TTS/LLM stay
unwrapped — Pipecat's own service objects remain the Broker layer per a
pre-existing decision; investigated pipecat 1.8.1's actual source and kept
AzureTTSService (SDK, streaming) over the REST AzureHttpTTSService after a
latency trade-off (STT can't move off its SDK either way, so REST wouldn't
even remove the native-dependency cost). Wrote 6 draft files this
session — 2 of them (prompts.py, session_log.py) are intermediate and will
be deleted once their Brokers exist; pipeline_builder.py still imports the
old shape and needs rework. Committed f02a49d (WIP, not the final shape).
Created a target-architecture canvas:
Projects/spanish-companion/voice-conversation-architecture.canvas. Full
record:
Projects/spanish-companion/decisions/voice-conversation-broker-service-split.md.
Not hardware-tested — nothing in this session's draft is trusted until a
real mic test, per CLAUDE.md's standing Voice Conversation waiver.

---

## Entity Manifest

| Feature | Path |
| --- | --- |
| SessionLifecycle | Projects/spanish-companion/entities/session-lifecycle.md |
| VoiceConversation | Projects/spanish-companion/entities/voice-conversation.md |
| Ingestion | Projects/spanish-companion/entities/ingestion.md |
| Retrieval | Projects/spanish-companion/entities/retrieval.md |
| Generation | Projects/spanish-companion/entities/generation.md |
| Review | Projects/spanish-companion/entities/review.md |

---

## Vault Structure Reference

| Location | Path | What lives there |
| --- | --- | --- |
| Project state | Projects/spanish-companion/state.md | MVP stage tracker, pending work, last session pointer |
| Session summaries | Projects/spanish-companion/sessions/ | One file per session — YYYY-MM-DD-HHmm.md |
| Architectural decisions | Projects/spanish-companion/decisions/ | One file per decision — kebab-case slug |
