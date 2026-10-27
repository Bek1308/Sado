import logging
from collections.abc import Callable
from dataclasses import dataclass

from sado.domain.audio import Audio
from sado.domain.speech import SpeechSynthesizer
from sado.domain.voice import Voice

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class TransliteratingSynthesizer:
    """Converts text to the script a speech model was trained on, e.g. Uzbek Latin to Cyrillic."""

    inner: SpeechSynthesizer
    transliterate: Callable[[str], str]

    def synthesize(self, text: str, voice: Voice) -> Audio:
        return self.inner.synthesize(self.transliterate(text), voice)


@dataclass(frozen=True, slots=True)
class FallbackSynthesizer:
    """Keeps Sado talking when the preferred voice fails, e.g. the GPU is busy or out of memory."""

    primary: SpeechSynthesizer
    fallback: SpeechSynthesizer

    def synthesize(self, text: str, voice: Voice) -> Audio:
        try:
            return self.primary.synthesize(text, voice)
        except Exception:
            logger.exception("Primary voice failed; speaking with the fallback voice")
            return self.fallback.synthesize(text, voice)
