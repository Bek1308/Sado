from dataclasses import dataclass, field

from sado.application.voices import VoiceCatalog
from sado.domain.audio import Audio
from sado.domain.language import Language
from sado.domain.mood import Mood
from sado.domain.recording import Recording, Transcript
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
    moods: list[Mood] = field(default_factory=list)

    def synthesize(self, text: str, voice: Voice, mood: Mood) -> Audio:
        self.spoken.append((text, voice.id))
        self.moods.append(mood)
        return Audio(wav_bytes=f"wav:{voice.id}:{text}".encode())


@dataclass
class EchoRecognizer:
    """Pretends the recording's bytes are the words that were spoken."""

    heard: list[Recording] = field(default_factory=list)

    def transcribe(self, recording: Recording) -> Transcript:
        self.heard.append(recording)
        return Transcript(text=recording.data.decode())


def fake_language_pack(language: Language) -> tuple[LanguagePack, RecordingSynthesizer]:
    synthesizer = RecordingSynthesizer()
    return LanguagePack(language, UppercaseNormalizer(), synthesizer, EchoRecognizer()), synthesizer
