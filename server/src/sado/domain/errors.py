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


class EmptyPaperError(SadoError):
    def __init__(self) -> None:
        super().__init__("The upload contains no file")


class UnsupportedPaperError(SadoError):
    def __init__(self, media_type: str) -> None:
        super().__init__(
            f"Cannot explain '{media_type}'; send a photo (JPEG, PNG, GIF, WebP), "
            "an audio or video recording, or a text, PDF, Word, Excel, PowerPoint, "
            "OpenDocument or HTML file"
        )
        self.media_type = media_type


class UnreadablePaperError(SadoError):
    def __init__(self) -> None:
        super().__init__("No readable text found in this file; photograph its pages instead")


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


class EmptyReminderError(SadoError):
    def __init__(self) -> None:
        super().__init__("There is nothing to remind about")


class InvalidReminderDueError(SadoError):
    def __init__(self, due: str) -> None:
        super().__init__(f"Cannot understand the due time '{due}'")
        self.due = due


class UnknownReminderError(SadoError):
    def __init__(self, reminder_id: str) -> None:
        super().__init__(f"No reminder with id '{reminder_id}'")
        self.reminder_id = reminder_id


class UnreadableRecordingError(SadoError):
    """The recording reached speech recognition but could not be understood as audio."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"Sado could not hear that recording: {reason}")


class SpeechSynthesisUnavailableError(SadoError):
    """No voice engine could speak the text."""

    def __init__(self) -> None:
        super().__init__("Sado cannot speak right now; please try again")
