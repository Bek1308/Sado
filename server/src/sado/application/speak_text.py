import logging
from collections.abc import Mapping

from sado.application.voices import VoiceCatalog
from sado.domain.audio import Audio
from sado.domain.errors import (
    EmptyTextError,
    SadoError,
    SpeechSynthesisUnavailableError,
    UnsupportedLanguageError,
)
from sado.domain.expression import remove_expression_cues
from sado.domain.language import Language
from sado.domain.mood import Mood
from sado.domain.speech import LanguagePack

logger = logging.getLogger(__name__)


class SpeakText:
    def __init__(
        self, language_packs: Mapping[Language, LanguagePack], voices: VoiceCatalog
    ) -> None:
        self._language_packs = language_packs
        self._voices = voices

    def execute(
        self,
        text: str,
        language: Language,
        voice_id: str | None = None,
        mood: Mood = Mood.NEUTRAL,
    ) -> Audio:
        stripped_text = text.strip()
        if not stripped_text:
            raise EmptyTextError

        pack = self._language_packs.get(language)
        if pack is None:
            raise UnsupportedLanguageError(language)

        # A reply made only of cues, e.g. "[laugh]", has nothing left for a voice to say.
        if not remove_expression_cues(stripped_text).strip():
            raise EmptyTextError
        voice = self._voices.find(voice_id)
        spoken_text = pack.normalizer.normalize(stripped_text)
        try:
            return pack.synthesizer.synthesize(spoken_text, voice, mood)
        except SadoError:
            raise
        except Exception as error:
            # Voice engines fail in many ways (model download, GPU memory); callers only
            # need to know Sado cannot speak right now.
            logger.exception("Every voice engine failed")
            raise SpeechSynthesisUnavailableError from error
