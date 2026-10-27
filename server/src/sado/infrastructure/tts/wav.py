import io
import wave
from collections.abc import Sequence

_PCM16_MAX = 32_767
_PCM16_SAMPLE_WIDTH_BYTES = 2


def encode_pcm16_wav(samples: Sequence[float], sample_rate: int) -> bytes:
    """Encode mono samples in the range [-1.0, 1.0] as a 16-bit PCM WAV file."""
    frames = bytearray()
    for sample in samples:
        clipped = max(-1.0, min(1.0, sample))
        frames += int(clipped * _PCM16_MAX).to_bytes(
            _PCM16_SAMPLE_WIDTH_BYTES, "little", signed=True
        )

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(_PCM16_SAMPLE_WIDTH_BYTES)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(bytes(frames))
    return buffer.getvalue()
