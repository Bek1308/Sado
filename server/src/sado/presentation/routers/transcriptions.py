from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from sado.application.transcribe_speech import TranscribeSpeech
from sado.domain.language import Language
from sado.domain.recording import Recording
from sado.presentation.dependencies import get_transcribe_speech

router = APIRouter(prefix="/transcriptions", tags=["speech"])

_MAX_RECORDING_BYTES = 10 * 1024 * 1024
_DEFAULT_MEDIA_TYPE = "application/octet-stream"


class TranscriptionResponse(BaseModel):
    text: str
    language: Language


@router.post("")
def transcribe(
    audio: UploadFile,
    transcribe_speech: Annotated[TranscribeSpeech, Depends(get_transcribe_speech)],
    language: Annotated[Language | None, Form()] = None,
) -> TranscriptionResponse:
    data = audio.file.read(_MAX_RECORDING_BYTES + 1)
    if len(data) > _MAX_RECORDING_BYTES:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "Recording is larger than 10 MB")

    recording = Recording(data=data, media_type=audio.content_type or _DEFAULT_MEDIA_TYPE)
    if language is None:
        transcript, detected = transcribe_speech.execute_auto(recording)
        return TranscriptionResponse(text=transcript.text, language=detected)
    transcript = transcribe_speech.execute(recording, language)
    return TranscriptionResponse(text=transcript.text, language=language)
