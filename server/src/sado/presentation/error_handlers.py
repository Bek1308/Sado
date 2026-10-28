from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from sado.domain.errors import (
    EmptyMemoryError,
    EmptyPaperError,
    EmptyRecordingError,
    EmptyReminderError,
    EmptyTextError,
    InvalidReminderDueError,
    NothingToAnswerError,
    ReasoningUnavailableError,
    SadoError,
    SpeechRecognitionUnavailableError,
    UnknownMemoryError,
    UnknownReminderError,
    UnknownVoiceError,
    UnreadablePaperError,
    UnsupportedLanguageError,
    UnsupportedPaperError,
)

_STATUS_BY_ERROR: dict[type[SadoError], int] = {
    EmptyTextError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    UnsupportedLanguageError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    UnknownVoiceError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    EmptyRecordingError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    EmptyPaperError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    UnsupportedPaperError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    UnreadablePaperError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    SpeechRecognitionUnavailableError: status.HTTP_503_SERVICE_UNAVAILABLE,
    NothingToAnswerError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    ReasoningUnavailableError: status.HTTP_503_SERVICE_UNAVAILABLE,
    EmptyMemoryError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    UnknownMemoryError: status.HTTP_404_NOT_FOUND,
    EmptyReminderError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    InvalidReminderDueError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    UnknownReminderError: status.HTTP_404_NOT_FOUND,
}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(SadoError)
    def handle_sado_error(_: Request, error: SadoError) -> JSONResponse:
        status_code = _STATUS_BY_ERROR.get(type(error), status.HTTP_400_BAD_REQUEST)
        return JSONResponse(status_code=status_code, content={"detail": str(error)})
