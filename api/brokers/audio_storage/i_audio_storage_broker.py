"""Broker interface for session-audio file storage (roadmap E3).

`typing.Protocol` per CLAUDE.md's Broker-interfaces waiver. Raw file I/O only.
"""

from typing import Protocol


class IAudioStorageBroker(Protocol):
    """External-resource boundary for the local-disk WAV store. No business
    logic; lets OSError propagate unmodified."""

    def write_wav(self, file_name: str, pcm: bytes, sample_rate: int, num_channels: int) -> str:
        """Write 16-bit PCM `pcm` as a WAV named `file_name` (directory
        components are stripped) and return the file's full path."""
        ...

    def delete_file(self, file_path: str) -> None:
        """Delete the file; a file that is already gone is not an error."""
        ...
