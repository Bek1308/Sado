from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, slots=True)
class Audio:
    wav_bytes: bytes

    media_type: ClassVar[str] = "audio/wav"
