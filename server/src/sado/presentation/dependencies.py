from typing import cast

from fastapi import Request

from sado.application.speak_text import SpeakText


def get_speak_text(request: Request) -> SpeakText:
    return cast(SpeakText, request.app.state.speak_text)
