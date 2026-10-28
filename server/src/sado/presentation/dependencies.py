from typing import cast

from fastapi import Request

from sado.application.converse import Converse
from sado.application.memories import Memories
from sado.application.speak_text import SpeakText
from sado.application.transcribe_speech import TranscribeSpeech
from sado.application.voices import VoiceCatalog


def get_converse(request: Request) -> Converse:
    return cast(Converse, request.app.state.converse)


def get_memories(request: Request) -> Memories:
    return cast(Memories, request.app.state.memories)


def get_speak_text(request: Request) -> SpeakText:
    return cast(SpeakText, request.app.state.speak_text)


def get_transcribe_speech(request: Request) -> TranscribeSpeech:
    return cast(TranscribeSpeech, request.app.state.transcribe_speech)


def get_voice_catalog(request: Request) -> VoiceCatalog:
    return cast(VoiceCatalog, request.app.state.voice_catalog)
