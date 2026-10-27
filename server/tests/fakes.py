from dataclasses import dataclass, field

from sado.domain.audio import Audio
from sado.domain.language import Language
from sado.domain.speech import LanguagePack


class UppercaseNormalizer:
    def normalize(self, text: str) -> str:
        return text.upper()


@dataclass
class RecordingSynthesizer:
    spoken_texts: list[str] = field(default_factory=list)

    def synthesize(self, text: str) -> Audio:
        self.spoken_texts.append(text)
        return Audio(wav_bytes=f"wav:{text}".encode())


def fake_language_pack(language: Language) -> tuple[LanguagePack, RecordingSynthesizer]:
    synthesizer = RecordingSynthesizer()
    return LanguagePack(language, UppercaseNormalizer(), synthesizer), synthesizer
