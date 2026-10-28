from collections.abc import Mapping

from sado.domain.errors import EmptyRecordingError, UnsupportedLanguageError
from sado.domain.language import Language
from sado.domain.recording import Recording, Transcript
from sado.domain.speech import LanguagePack


class TranscribeSpeech:
    def __init__(self, language_packs: Mapping[Language, LanguagePack]) -> None:
        self._language_packs = language_packs

    def execute(self, recording: Recording, language: Language) -> Transcript:
        if not recording.data:
            raise EmptyRecordingError

        pack = self._language_packs.get(language)
        if pack is None:
            raise UnsupportedLanguageError(language)

        return pack.recognizer.transcribe(recording)
