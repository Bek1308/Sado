from collections.abc import Sequence
from dataclasses import dataclass

from sado.domain.errors import UnknownVoiceError
from sado.domain.voice import Voice


@dataclass(frozen=True, slots=True)
class VoiceCatalog:
    voices: Sequence[Voice]
    default: Voice

    def __post_init__(self) -> None:
        if self.default not in self.voices:
            raise ValueError("The default voice must be one of the catalog voices")

    def find(self, voice_id: str | None) -> Voice:
        if voice_id is None:
            return self.default
        for voice in self.voices:
            if voice.id == voice_id:
                return voice
        raise UnknownVoiceError(voice_id)
