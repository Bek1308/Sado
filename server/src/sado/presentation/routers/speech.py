from typing import Annotated

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field

from sado.application.speak_text import SpeakText
from sado.domain.audio import Audio
from sado.domain.language import Language
from sado.presentation.dependencies import get_speak_text

router = APIRouter(prefix="/speech", tags=["speech"])

_MAX_TEXT_LENGTH = 1_000


class SpeakRequest(BaseModel):
    text: str = Field(min_length=1, max_length=_MAX_TEXT_LENGTH)
    language: Language
    voice: str | None = None


@router.post(
    "",
    response_class=Response,
    responses={200: {"content": {Audio.media_type: {}}, "description": "Spoken audio"}},
)
def speak(
    request: SpeakRequest,
    speak_text: Annotated[SpeakText, Depends(get_speak_text)],
) -> Response:
    audio = speak_text.execute(request.text, request.language, request.voice)
    return Response(content=audio.wav_bytes, media_type=Audio.media_type)
