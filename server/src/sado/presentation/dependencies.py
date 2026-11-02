import secrets
from dataclasses import dataclass
from typing import cast

from fastapi import Request

from sado.application.converse import Converse
from sado.application.desktop_tools import PendingActions
from sado.application.explain_document import ExplainDocument
from sado.application.lists import Lists
from sado.application.memories import Memories
from sado.application.reminders import Reminders
from sado.application.speak_text import SpeakText
from sado.application.transcribe_speech import TranscribeSpeech
from sado.application.voices import VoiceCatalog


@dataclass(frozen=True, slots=True)
class Space:
    """One person's Sado: what it remembers, the reminders and lists, and how it talks."""

    converse: Converse
    memories: Memories
    reminders: Reminders
    lists: Lists


def may_control_desktop(request: Request) -> bool:
    """Whether this request comes from a device trusted to drive the computer."""
    expected = cast(str, getattr(request.app.state, "desktop_token", ""))
    given = request.headers.get("X-Sado-Desktop-Token", "")
    return bool(expected) and secrets.compare_digest(expected, given)


def _space(request: Request) -> Space:
    # The owner's devices carry the desktop token; everyone else is a guest, so a tunnel
    # never shows the owner's memories to strangers.
    owner = cast(Space, request.app.state.owner)
    guest = cast(Space, request.app.state.guest)
    return owner if guest is owner or may_control_desktop(request) else guest


def get_converse(request: Request) -> Converse:
    return _space(request).converse


def get_explain_document(request: Request) -> ExplainDocument:
    return cast(ExplainDocument, request.app.state.explain_document)


def get_pending_actions(request: Request) -> PendingActions:
    return cast(PendingActions, request.app.state.pending_actions)


def get_lists(request: Request) -> Lists:
    return _space(request).lists


def get_memories(request: Request) -> Memories:
    return _space(request).memories


def get_reminders(request: Request) -> Reminders:
    return _space(request).reminders


def get_speak_text(request: Request) -> SpeakText:
    return cast(SpeakText, request.app.state.speak_text)


def get_transcribe_speech(request: Request) -> TranscribeSpeech:
    return cast(TranscribeSpeech, request.app.state.transcribe_speech)


def get_voice_catalog(request: Request) -> VoiceCatalog:
    return cast(VoiceCatalog, request.app.state.voice_catalog)
