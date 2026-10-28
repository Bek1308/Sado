from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from sado.application.explain_document import ExplainDocument
from sado.domain.language import Language
from sado.domain.vision import Paper
from sado.presentation.dependencies import get_explain_document

router = APIRouter(prefix="/explanations", tags=["vision"])

_MAX_FILE_BYTES = 10 * 1024 * 1024
_DEFAULT_MEDIA_TYPE = "application/octet-stream"


class ExplanationResponse(BaseModel):
    explanation: str
    language: Language


@router.post("")
def explain(
    file: UploadFile,
    language: Annotated[Language, Form()],
    explain_document: Annotated[ExplainDocument, Depends(get_explain_document)],
) -> ExplanationResponse:
    data = file.file.read(_MAX_FILE_BYTES + 1)
    if len(data) > _MAX_FILE_BYTES:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "File is larger than 10 MB")

    media_type = (file.content_type or _DEFAULT_MEDIA_TYPE).split(";")[0].strip().lower()
    explanation = explain_document.execute(Paper(data=data, media_type=media_type), language)
    return ExplanationResponse(explanation=explanation.text, language=language)
