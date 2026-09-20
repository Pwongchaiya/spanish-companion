"""Interface for the audio_storage Foundation service (roadmap E3).

typing.Protocol per this project's interface waiver. Every method raises
AudioStorageValidationException (wrapping InvalidAudioStorageException) on bad
input, AudioStorageDependencyException (wrapping FailedAudioStorageException)
if the broker's file I/O fails, and AudioStorageServiceException otherwise.
"""

from typing import Protocol


class IAudioStorageService(Protocol):
    """External-facing contract for the local-disk audio store."""

    def store_wav(self, file_name: str, pcm: bytes, sample_rate: int, num_channels: int) -> str:
        """Write 16-bit PCM as a WAV and return its path."""
        ...

    def remove_file(self, file_path: str) -> None:
        """Delete the file; already-gone is not an error."""
        ...
