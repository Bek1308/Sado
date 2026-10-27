from typing import cast

from fastapi import Request

from sado.application.speak_text import SpeakText
from sado.application.voices import VoiceCatalog


def get_speak_text(request: Request) -> SpeakText:
    return cast(SpeakText, request.app.state.speak_text)


def get_voice_catalog(request: Request) -> VoiceCatalog:
    return cast(VoiceCatalog, request.app.state.voice_catalog)
