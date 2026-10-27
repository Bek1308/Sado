from dataclasses import dataclass
from typing import Protocol

from sado.domain.audio import Audio
from sado.domain.language import Language


class TextNormalizer(Protocol):
    def normalize(self, text: str) -> str:
        """Rewrite text so a speech model reads it naturally (numbers become words, etc.)."""
        ...


class SpeechSynthesizer(Protocol):
    def synthesize(self, text: str) -> Audio: ...


@dataclass(frozen=True, slots=True)
class LanguagePack:
    """Everything Sado needs to speak one language. New languages are added as new packs."""

    language: Language
    normalizer: TextNormalizer
    synthesizer: SpeechSynthesizer
