"""Pure tick-to-byte slicing for pronunciation-capture spike (#69).

Azure Speech SDK reports `offset`/`duration` on a SpeechRecognitionResult in
100ns ticks (`frame.result.result.offset` / `.duration` on pipecat's
TranscriptionFrame — see docs/spikes/69-live-pronunciation-capture.md for the
verified frame path). This converts those ticks into a byte range that can
slice the whole-session PCM buffer captured by pipecat's AudioBufferProcessor
(see voice_conversation_service.py:705-722).

Sibling of _priming.py/_difficulty.py: one pure function, no I/O, no project
imports, assert-based __main__ self-check.

Clamping the returned byte range to the actual buffer length is the caller's
job — this function does not know the buffer's size.
"""

TICKS_PER_SECOND = 10_000_000  # Azure/.NET tick = 100ns


def slice_bytes(
    offset_ticks: int,
    duration_ticks: int,
    sample_rate: int,
    num_channels: int,
    sample_width: int = 2,
) -> tuple[int, int]:
    """Byte range (start, end) into a PCM buffer for the given tick offset/duration.

    Works in whole-sample-frame units first, then converts to bytes, so the
    result is always aligned to a frame boundary (frame = num_channels *
    sample_width bytes) by construction:
    - start is floored to the frame at or before the offset (never drops
      leading audio the offset points into).
    - duration is ceiling-rounded to at least one whole frame (never drops
      trailing audio, and a nonzero duration never collapses to a zero-length
      slice).

    Clamping to an actual buffer's length is the caller's responsibility.
    """
    frame_size = num_channels * sample_width
    start_frame = (offset_ticks * sample_rate) // TICKS_PER_SECOND
    duration_frames = -(-(duration_ticks * sample_rate) // TICKS_PER_SECOND)  # ceil div
    end_frame = start_frame + duration_frames
    return start_frame * frame_size, end_frame * frame_size


if __name__ == "__main__":
    # 1s duration at offset 0, 16kHz mono 16-bit -> exactly one second of bytes.
    assert slice_bytes(0, 10_000_000, 16000, 1, 2) == (0, 32000)
    # Default sample_width (2) matches the explicit case above.
    assert slice_bytes(0, 10_000_000, 16000, 1) == (0, 32000)
    # Non-frame-aligned offset/duration, stereo 16-bit: result must still be
    # a multiple of frame_size (4 bytes/frame here).
    start, end = slice_bytes(1234567, 100000, 16000, 2, 2)
    assert (start, end) == (7900, 8540)
    assert start % 4 == 0 and end % 4 == 0
    # A tiny nonzero duration still yields at least one full frame, not zero.
    assert slice_bytes(0, 1, 16000, 1, 2) == (0, 2)
    print("OK")
