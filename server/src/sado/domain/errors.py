from sado.domain.language import Language


class SadoError(Exception):
    """Base class for every error the domain and application layers raise on purpose."""


class EmptyTextError(SadoError):
    def __init__(self) -> None:
        super().__init__("Text must contain at least one non-whitespace character")


class UnsupportedLanguageError(SadoError):
    def __init__(self, language: Language) -> None:
        super().__init__(f"No language pack is available for '{language}'")
        self.language = language


class UnknownVoiceError(SadoError):
    def __init__(self, voice_id: str) -> None:
        super().__init__(f"There is no voice called '{voice_id}'")
        self.voice_id = voice_id


class EmptyRecordingError(SadoError):
    def __init__(self) -> None:
        super().__init__("The recording contains no audio")


class SpeechRecognitionUnavailableError(SadoError):
    """The speech recognition service could not be reached or failed."""

    def __init__(self) -> None:
        super().__init__("Speech recognition is temporarily unavailable")


class ReasoningUnavailableError(SadoError):
    """The reasoning model could not be reached or failed to answer."""

    def __init__(self) -> None:
        super().__init__("Sado cannot think right now; please try again")


class NothingToAnswerError(SadoError):
    def __init__(self) -> None:
        super().__init__("The conversation must end with a non-empty message from the user")


class EmptyMemoryError(SadoError):
    def __init__(self) -> None:
        super().__init__("There is nothing to remember")


class UnknownMemoryError(SadoError):
    def __init__(self, memory_id: str) -> None:
        super().__init__(f"No memory with id '{memory_id}'")
