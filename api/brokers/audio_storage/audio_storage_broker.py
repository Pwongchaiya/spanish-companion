"""LocalWavAudioStorageBroker -- stdlib `wave` writer under AUDIO_DIR."""

import os
import wave
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_AUDIO_DIR = REPO_ROOT / "data" / "audio"


class LocalWavAudioStorageBroker:
    """IAudioStorageBroker over a local directory (default AUDIO_DIR env, else
    <repo>/data/audio -- gitignored). Sample width is fixed at 16-bit: that is
    what Pipecat's audio buffer emits."""

    def __init__(self, audio_dir: Optional[Path] = None) -> None:
        self._audio_dir = audio_dir if audio_dir is not None else Path(os.getenv("AUDIO_DIR") or DEFAULT_AUDIO_DIR)

    def write_wav(self, file_name: str, pcm: bytes, sample_rate: int, num_channels: int) -> str:
        self._audio_dir.mkdir(parents=True, exist_ok=True)
        path = self._audio_dir / Path(file_name).name
        with wave.open(str(path), "wb") as wav:
            wav.setnchannels(num_channels)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(pcm)
        return str(path)

    def delete_file(self, file_path: str) -> None:
        Path(file_path).unlink(missing_ok=True)


if __name__ == "__main__":
    # ponytail: self-check -- round-trips a WAV through stdlib `wave`, checks
    # name sanitising and idempotent delete.
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        broker = LocalWavAudioStorageBroker(Path(tmp) / "audio")
        path = broker.write_wav("../evil/s1.wav", b"\x00\x01" * 24000, 24000, 1)
        assert Path(path).parent == Path(tmp) / "audio" and Path(path).name == "s1.wav", path
        with wave.open(path, "rb") as wav:
            assert (wav.getframerate(), wav.getnchannels(), wav.getnframes()) == (24000, 1, 24000)
        broker.delete_file(path)
        broker.delete_file(path)
        assert not Path(path).exists()
    print("audio_storage_broker self-check passed")
