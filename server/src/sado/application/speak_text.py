from collections.abc import Mapping

from sado.domain.audio import Audio
from sado.domain.errors import EmptyTextError, UnsupportedLanguageError
from sado.domain.language import Language
from sado.domain.speech import LanguagePack


class SpeakText:
    def __init__(self, language_packs: Mapping[Language, LanguagePack]) -> None:
        self._language_packs = language_packs

    def execute(self, text: str, language: Language) -> Audio:
        stripped_text = text.strip()
        if not stripped_text:
            raise EmptyTextError

        pack = self._language_packs.get(language)
        if pack is None:
            raise UnsupportedLanguageError(language)

        spoken_text = pack.normalizer.normalize(stripped_text)
        return pack.synthesizer.synthesize(spoken_text)
