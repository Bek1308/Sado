from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from sado.domain.errors import EmptyTextError, SadoError, UnsupportedLanguageError

_STATUS_BY_ERROR: dict[type[SadoError], int] = {
    EmptyTextError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    UnsupportedLanguageError: status.HTTP_422_UNPROCESSABLE_CONTENT,
}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(SadoError)
    def handle_sado_error(_: Request, error: SadoError) -> JSONResponse:
        status_code = _STATUS_BY_ERROR.get(type(error), status.HTTP_400_BAD_REQUEST)
        return JSONResponse(status_code=status_code, content={"detail": str(error)})
