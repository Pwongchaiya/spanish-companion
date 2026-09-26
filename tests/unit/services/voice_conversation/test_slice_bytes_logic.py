"""Unit tests for the free function slice_bytes.

Azure Speech Recognition reports offset/duration as 100-nanosecond ticks.
This utility converts tick-based timestamps into (start_byte, end_byte) ranges
into a PCM buffer, accounting for sample rate, channel count, and sample width.
Relates to issue #69: offset spike in pronunciation timing.
"""

from api.services.orchestrations.voice_conversation._pronunciation_offset import (
    slice_bytes,
)


class TestSliceBytes:
    def test_one_second_at_offset_zero_mono_16bit(self):
        start, end = slice_bytes(0, 10_000_000, 16000, 1, 2)

        assert (start, end) == (0, 32000)

    def test_default_sample_width_is_two_bytes(self):
        start, end = slice_bytes(0, 10_000_000, 16000, 1)

        assert (start, end) == (0, 32000)

    def test_aligns_to_frame_boundary_for_stereo_16bit(self):
        start, end = slice_bytes(1234567, 100000, 16000, 2, 2)

        assert (start, end) == (7900, 8540)
        assert start % 4 == 0
        assert end % 4 == 0

    def test_tiny_nonzero_duration_yields_at_least_one_frame(self):
        start, end = slice_bytes(0, 1, 16000, 1, 2)

        assert (start, end) == (0, 2)

    def test_end_is_never_before_start(self):
        start, end = slice_bytes(500000, 20000, 16000, 1, 2)

        assert end >= start


if __name__ == "__main__":
    import subprocess
    import sys

    raise SystemExit(subprocess.call([sys.executable, "-m", "pytest", __file__, "-q"]))
