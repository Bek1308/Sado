import secrets
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import cast

from fastapi import Request

from sado.application.converse import Converse
from sado.application.desktop_tools import PendingActions
from sado.application.explain_document import ExplainDocument
from sado.application.lists import Lists
from sado.application.memories import Memories
from sado.application.phone_inbox import PhoneInbox
from sado.application.reminders import Reminders
from sado.application.speak_text import SpeakText
from sado.application.transcribe_speech import TranscribeSpeech
from sado.application.voices import VoiceCatalog
from sado.domain.identity import IdentityVerifier, Person


@dataclass(frozen=True, slots=True)
class Space:
    """One person's Sado: what it remembers, the reminders and lists, and how it talks."""

    converse: Converse
    memories: Memories
    reminders: Reminders
    lists: Lists


@dataclass(slots=True)
class PersonalSpaces:
    """A Space for everyone who signs in with Google, opened on their first visit."""

    open_space: Callable[[str], Space]
    _spaces: dict[str, Space] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def of(self, person: Person) -> Space:
        with self._lock:
            if person.id not in self._spaces:
                self._spaces[person.id] = self.open_space(person.id)
            return self._spaces[person.id]


def signed_in(request: Request) -> Person | None:
    """Who signed in on the device asking, if anyone; a bad sign-in is an error."""
    header = request.headers.get("Authorization", "")
    verifier = cast(IdentityVerifier | None, getattr(request.app.state, "identity", None))
    if verifier is None or not header.startswith("Bearer "):
        return None
    if not hasattr(request.state, "person"):
        request.state.person = verifier.verify(header.removeprefix("Bearer ").strip())
    return cast(Person, request.state.person)


def at_the_computer(request: Request) -> bool:
    """Whether the request comes from the Sado app on the owner's computer itself."""
    expected = cast(str, getattr(request.app.state, "desktop_token", ""))
    given = request.headers.get("X-Sado-Desktop-Token", "")
    return bool(expected) and secrets.compare_digest(expected, given)


def is_owner(request: Request) -> bool:
    """The owner talks from their computer, or from a phone signed in to their account."""
    if at_the_computer(request):
        return True
    person = signed_in(request)
    owners = cast(frozenset[str], getattr(request.app.state, "owner_emails", frozenset()))
    return person is not None and person.email is not None and person.email.lower() in owners


def may_control_desktop(request: Request) -> bool:
    """Whether this request may drive the computer: only the owner's, and only if Sado
    has a computer to drive."""
    return bool(getattr(request.app.state, "desktop_token", "")) and is_owner(request)


def _space(request: Request) -> Space:
    # Strangers never see the owner's memories: everyone signed in gets their own, and
    # devices that did not sign in share a guest space.
    owner = cast(Space, request.app.state.owner)
    guest = cast(Space, request.app.state.guest)
    if guest is owner or is_owner(request):
        return owner
    person = signed_in(request)
    people = cast(PersonalSpaces | None, getattr(request.app.state, "people", None))
    if person is not None and people is not None:
        return people.of(person)
    return guest


def get_converse(request: Request) -> Converse:
    return _space(request).converse


def get_explain_document(request: Request) -> ExplainDocument:
    return cast(ExplainDocument, request.app.state.explain_document)


def get_pending_actions(request: Request) -> PendingActions:
    return cast(PendingActions, request.app.state.pending_actions)


def get_phone_inbox(request: Request) -> PhoneInbox:
    return cast(PhoneInbox, request.app.state.phone_inbox)


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
