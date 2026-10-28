from collections.abc import Mapping

from sado.domain.errors import EmptyRecordingError, UnsupportedLanguageError
from sado.domain.language import Language
from sado.domain.language_detect import detect_language
from sado.domain.recording import Recording, Transcript
from sado.domain.speech import LanguagePack


class TranscribeSpeech:
    def __init__(self, language_packs: Mapping[Language, LanguagePack]) -> None:
        self._language_packs = language_packs
        self._last_detected = next(iter(language_packs), Language.TAJIK)

    def execute(self, recording: Recording, language: Language) -> Transcript:
        if not recording.data:
            raise EmptyRecordingError

        pack = self._language_packs.get(language)
        if pack is None:
            raise UnsupportedLanguageError(language)

        return pack.recognizer.transcribe(recording)

    def execute_auto(self, recording: Recording) -> tuple[Transcript, Language]:
        """Transcribe without a known language; returns the transcript and the language found.

        The recognizer needs an explicit language, so candidates are tried starting
        with the last detected language — repeat callers usually cost one pass.
        The first transcript whose own words match the requested language wins.
        """
        if not recording.data:
            raise EmptyRecordingError

        candidates = [
            language for language in self._preferred_order() if language in self._language_packs
        ]
        if not candidates:
            raise UnsupportedLanguageError(self._last_detected)

        heard: list[tuple[Transcript, Language | None]] = []
        for language in candidates:
            transcript = self._language_packs[language].recognizer.transcribe(recording)
            # Silence or a single word carries no language signal; more passes would only
            # cost time and hear the same nothing.
            if len(transcript.text.split()) <= 1:
                self._last_detected = language
                return transcript, language
            detected = detect_language(transcript.text)
            if detected is language:
                self._last_detected = language
                return transcript, language
            heard.append((transcript, detected))

        for transcript, detected in heard:
            if detected is not None:
                self._last_detected = detected
                return transcript, detected
        self._last_detected = candidates[0]
        return heard[0][0], candidates[0]

    def _preferred_order(self) -> list[Language]:
        return [
            self._last_detected,
            *(language for language in Language if language is not self._last_detected),
        ]
