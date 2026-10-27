import logging
from collections.abc import Callable
from dataclasses import dataclass

from sado.domain.audio import Audio
from sado.domain.expression import remove_expression_cues
from sado.domain.mood import Mood
from sado.domain.speech import SpeechSynthesizer
from sado.domain.voice import Voice

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class TransliteratingSynthesizer:
    """Converts text to the script a speech model was trained on, e.g. Uzbek Latin to Cyrillic."""

    inner: SpeechSynthesizer
    transliterate: Callable[[str], str]

    def synthesize(self, text: str, voice: Voice, mood: Mood) -> Audio:
        return self.inner.synthesize(self.transliterate(text), voice, mood)


@dataclass(frozen=True, slots=True)
class CueFreeSynthesizer:
    """Drops expression cues for engines that would otherwise read "[laugh]" aloud."""

    inner: SpeechSynthesizer

    def synthesize(self, text: str, voice: Voice, mood: Mood) -> Audio:
        return self.inner.synthesize(remove_expression_cues(text), voice, mood)


@dataclass(frozen=True, slots=True)
class FallbackSynthesizer:
    """Keeps Sado talking when the preferred voice fails, e.g. the GPU is busy or out of memory."""

    primary: SpeechSynthesizer
    fallback: SpeechSynthesizer

    def synthesize(self, text: str, voice: Voice, mood: Mood) -> Audio:
        try:
            return self.primary.synthesize(text, voice, mood)
        except Exception:
            logger.exception("Primary voice failed; speaking with the fallback voice")
            return self.fallback.synthesize(text, voice, mood)
