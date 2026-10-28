from dataclasses import dataclass
from typing import Protocol

from sado.domain.audio import Audio
from sado.domain.language import Language
from sado.domain.mood import Mood
from sado.domain.recording import Recording, Transcript
from sado.domain.voice import Voice


class TextNormalizer(Protocol):
    def normalize(self, text: str) -> str:
        """Rewrite text so a speech model reads it naturally (numbers become words, etc.)."""
        ...


class SpeechSynthesizer(Protocol):
    def synthesize(self, text: str, voice: Voice, mood: Mood) -> Audio: ...


class SpeechRecognizer(Protocol):
    def transcribe(self, recording: Recording) -> Transcript: ...


@dataclass(frozen=True, slots=True)
class LanguagePack:
    """Everything Sado needs to hear and speak one language. New languages are new packs."""

    language: Language
    normalizer: TextNormalizer
    synthesizer: SpeechSynthesizer
    recognizer: SpeechRecognizer
