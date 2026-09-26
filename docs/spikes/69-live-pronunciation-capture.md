# Spike: live-conversation pronunciation capture (#69)

## Question

Can the voice pipeline capture *which audio corresponds to which
transcript*, precisely enough to later score pronunciation, without adding
any per-utterance cost (RAG, verify) to Conversation Mode? Scope for this
spike is timing capture only — scoring approach is still open.

## Verified frame path (pipecat 1.11.0, re-checked against prior 1.8.1 notes)

- `AzureSTTService._on_handle_recognized` builds
  `TranscriptionFrame(event.result.text, ..., result=event, finalized=True)`
  — `.venv/Lib/site-packages/pipecat/services/azure/stt.py:388-395` (the
  `result=event` kwarg is line 393). `event` is Azure's
  `SpeechRecognitionEventArgs`, so the tick offset/duration are one level
  deeper than the frame's own `.result`: **`frame.result.result.offset`** /
  **`frame.result.result.duration`**. Confirmed unchanged from the 1.8.1
  finding.
- Sample width: `AudioRawFrame.__post_init__` computes
  `num_frames = int(len(self.audio) / (self.num_channels * 2))` —
  `pipecat/frames/frames.py:177`. The hardcoded `2` confirms pipecat's whole
  audio-frame model assumes 16-bit (2-byte) PCM samples; nothing overrides
  this for Azure STT or `AudioBufferProcessor` input/output frames.
- E3 session capture: `AudioBufferProcessor(num_channels=1, ...)` and its
  `on_audio_data(_buffer, audio: bytes, sample_rate: int, num_channels: int)`
  handler — `voice_conversation_service.py:715-718` (unchanged from prior
  notes; `AlwaysUserMuteStrategy` still at `:594`, no pipeline edits made in
  this spike).

## Recommended: Option A — passthrough processor, slice at teardown

Insert a thin `FrameProcessor` between the STT service and the user context
aggregator. It doesn't transform frames — just observes `TranscriptionFrame`s
as they pass and appends `(text, offset_ticks, duration_ticks)` to an
in-memory list, then forwards the frame unchanged. Zero added latency, zero
RAG/verify calls — satisfies the "Conversation Mode stays fast" constraint.

At pipeline teardown, when E3's `on_audio_data` fires with the whole-session
PCM buffer, run each recorded `(offset_ticks, duration_ticks)` through this
spike's new `slice_bytes()` (`api/services/orchestrations/voice_conversation/
_pronunciation_offset.py`) against that session's `sample_rate`/`num_channels`
to get byte ranges, clamp each to `len(audio)` (the function deliberately
doesn't clamp — session-level concern, not a pure-function one), and persist
the per-utterance audio clips. Scoring itself happens later, in Review Mode,
where cost is already accepted.

## Rejected alternatives

- **B — per-utterance capture inside Conversation Mode** (slice audio the
  moment each `TranscriptionFrame` arrives, no session-wide buffer). Rejected:
  needs its own rolling audio buffer instead of reusing E3's existing
  session-wide `AudioBufferProcessor` — no benefit over Option A, strictly
  more state during the timing-sensitive live loop.
- **C — score during Conversation Mode** (call a pronunciation model inline
  per utterance). Rejected outright: violates this project's core design
  principle — nothing expensive runs live in Conversation Mode.

## Open product question: reference-text bias

Every practical pronunciation-scoring approach (Azure's own pronunciation
assessment, wav2vec-CTC alignment, etc.) needs a *reference* transcript.
Using the STT's own output as that reference is circular — it grades audio
against what the STT already believed it heard, so mis-recognitions never
surface as pronunciation errors. Whether Review Mode should re-prompt the
learner with the intended sentence, or accept this bias, is a product call
outside this spike's scope.

## Checks that need a real mic (can't verify from code alone)

- Confirm `frame.result.result.offset`/`.duration` are actually populated
  (non-zero, monotonic) on a live Azure recognition, not just present on the
  Python object.
- Clock drift: whether STT's tick offsets and E3's captured sample count
  agree on where an utterance falls, once VAD/turn-taking pauses and Azure's
  own internal buffering are in play — the sample-accurate math above trusts
  offsets that are only as accurate as Azure's clock vs. the transport's.
- Whether `AlwaysUserMuteStrategy` (`:594`) drops frames during the
  passthrough processor's window, leaving gaps vs. the E3 buffer.
