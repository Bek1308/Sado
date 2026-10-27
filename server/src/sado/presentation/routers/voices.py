from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from sado.application.voices import VoiceCatalog
from sado.presentation.dependencies import get_voice_catalog

router = APIRouter(prefix="/voices", tags=["voices"])


class VoiceResponse(BaseModel):
    id: str
    name: str
    is_default: bool


@router.get("")
def list_voices(
    catalog: Annotated[VoiceCatalog, Depends(get_voice_catalog)],
) -> list[VoiceResponse]:
    return [
        VoiceResponse(id=voice.id, name=voice.name, is_default=voice == catalog.default)
        for voice in catalog.voices
    ]
