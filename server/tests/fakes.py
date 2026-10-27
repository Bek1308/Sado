from dataclasses import dataclass, field

from sado.application.voices import VoiceCatalog
from sado.domain.audio import Audio
from sado.domain.language import Language
from sado.domain.speech import LanguagePack
from sado.domain.voice import Voice

SADO_VOICE = Voice("sado", "Sado")
OPA_VOICE = Voice("opa", "Opa")


def fake_voice_catalog() -> VoiceCatalog:
    return VoiceCatalog(voices=[SADO_VOICE, OPA_VOICE], default=SADO_VOICE)


class UppercaseNormalizer:
    def normalize(self, text: str) -> str:
        return text.upper()


@dataclass
class RecordingSynthesizer:
    spoken: list[tuple[str, str]] = field(default_factory=list)
    """Every (text, voice id) pair this synthesizer was asked to speak."""

    def synthesize(self, text: str, voice: Voice) -> Audio:
        self.spoken.append((text, voice.id))
        return Audio(wav_bytes=f"wav:{voice.id}:{text}".encode())


def fake_language_pack(language: Language) -> tuple[LanguagePack, RecordingSynthesizer]:
    synthesizer = RecordingSynthesizer()
    return LanguagePack(language, UppercaseNormalizer(), synthesizer), synthesizer
