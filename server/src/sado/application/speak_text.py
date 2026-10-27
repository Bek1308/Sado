from collections.abc import Mapping

from sado.application.voices import VoiceCatalog
from sado.domain.audio import Audio
from sado.domain.errors import EmptyTextError, UnsupportedLanguageError
from sado.domain.language import Language
from sado.domain.speech import LanguagePack


class SpeakText:
    def __init__(
        self, language_packs: Mapping[Language, LanguagePack], voices: VoiceCatalog
    ) -> None:
        self._language_packs = language_packs
        self._voices = voices

    def execute(self, text: str, language: Language, voice_id: str | None = None) -> Audio:
        stripped_text = text.strip()
        if not stripped_text:
            raise EmptyTextError

        pack = self._language_packs.get(language)
        if pack is None:
            raise UnsupportedLanguageError(language)

        voice = self._voices.find(voice_id)
        spoken_text = pack.normalizer.normalize(stripped_text)
        return pack.synthesizer.synthesize(spoken_text, voice)
