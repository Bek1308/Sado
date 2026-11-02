"""Composition root: the only place where layers are wired together."""

import importlib
import logging
import re
import threading
from collections.abc import AsyncIterator, Mapping, Sequence
from contextlib import asynccontextmanager
from pathlib import Path
from typing import cast

import httpx
from fastapi import FastAPI
from pydantic import SecretStr

from sado.application.converse import Converse
from sado.application.desktop_tools import DesktopTools, PendingActions
from sado.application.explain_document import ExplainDocument
from sado.application.lists import Lists
from sado.application.memories import Memories
from sado.application.phone_inbox import PhoneInbox
from sado.application.reminders import Reminders
from sado.application.speak_text import SpeakText
from sado.application.transcribe_speech import TranscribeSpeech
from sado.application.voices import VoiceCatalog
from sado.domain.conversation import ReasoningModel
from sado.domain.desktop import Desktop
from sado.domain.errors import InvalidIdentityError, SadoError
from sado.domain.identity import IdentityVerifier
from sado.domain.language import Language
from sado.domain.lists import ListStore
from sado.domain.memory import MemoryStore
from sado.domain.reminder import ReminderStore
from sado.domain.search import WebSearch
from sado.domain.speech import LanguagePack
from sado.domain.vision import DocumentExplainer
from sado.infrastructure.documents.readers import CompositeDocumentReader
from sado.infrastructure.identity.firebase_identity import FirebaseIdentity
from sado.infrastructure.languages.packs import (
    BackupListener,
    VoiceConfig,
    build_language_packs,
)
from sado.infrastructure.memory.sqlite_lists import SqliteListStore
from sado.infrastructure.memory.sqlite_reminders import SqliteReminderStore
from sado.infrastructure.memory.sqlite_store import SqliteMemoryStore
from sado.infrastructure.reasoning.muse_search import MuseWebSearch
from sado.infrastructure.reasoning.muse_spark import MuseSparkReasoner
from sado.infrastructure.reasoning.unavailable import UnavailableReasoner
from sado.infrastructure.settings import Settings, get_settings
from sado.infrastructure.tts.mms import VitsVoiceSettings
from sado.infrastructure.tts.omnivoice import CloneQuality
from sado.infrastructure.tts.voice_presets import VOICE_PRESETS
from sado.presentation.dependencies import PersonalSpaces, Space
from sado.presentation.error_handlers import register_error_handlers
from sado.presentation.routers import (
    actions,
    explanations,
    health,
    lists,
    memories,
    phone,
    reminders,
    replies,
    speech,
    transcriptions,
    voices,
)


def _voice_catalog(default_voice_id: str) -> VoiceCatalog:
    all_voices = [preset.voice for preset in VOICE_PRESETS]
    default = next(voice for voice in all_voices if voice.id == default_voice_id)
    return VoiceCatalog(voices=all_voices, default=default)


def _voice_config(settings: Settings) -> VoiceConfig:
    return VoiceConfig(
        use_omnivoice=settings.use_omnivoice,
        omnivoice_device=settings.omnivoice_device,
        omnivoice_uzbek_code=settings.omnivoice_uzbek_code,
        voice_styles={preset.voice.id: preset.style for preset in VOICE_PRESETS},
        mood_reference_dir=Path(settings.mood_reference_dir),
        clone_quality=CloneQuality(
            num_steps=settings.clone_num_steps, guidance_scale=settings.clone_guidance_scale
        ),
        mms_device=settings.mms_device,
        mms_voice=VitsVoiceSettings(
            speaking_rate=settings.voice_speaking_rate,
            pitch_variation=settings.voice_pitch_variation,
            rhythm_variation=settings.voice_rhythm_variation,
        ),
        asr_url=settings.asr_url,
        asr_timeout_seconds=settings.asr_timeout_seconds,
    )


def _desktop(settings: Settings) -> Desktop | None:
    if not settings.desktop_control:
        return None
    if not _secret(settings.desktop_token):
        logger.warning("Desktop control needs SADO_DESKTOP_TOKEN; leaving it off")
        return None
    # Imported only when asked for: it needs Windows and the optional `desktop` extra.
    from sado.infrastructure.desktop.windows_desktop import WindowsDesktop  # noqa: PLC0415

    return WindowsDesktop()


def _secret(value: SecretStr | None) -> str:
    return value.get_secret_value().strip() if value else ""


def _model_api(settings: Settings) -> httpx.Client | None:
    api_key = settings.meta_api_key.get_secret_value() if settings.meta_api_key else ""
    # A blank key, as copied from .env.example, means "not configured" rather than a bad key.
    if not api_key.strip():
        return None
    return httpx.Client(
        base_url=settings.meta_api_url,
        headers={"Authorization": f"Bearer {api_key.strip()}"},
        timeout=settings.reasoning_timeout_seconds,
    )


def _backup_listener(settings: Settings, model_api: httpx.Client | None) -> BackupListener | None:
    # Muse Spark Open on Baseten hears reliably; Muse on the Model API often misses audio.
    if baseten_key := _secret(settings.baseten_api_key):
        http = httpx.Client(
            base_url=settings.baseten_url,
            headers={"Authorization": f"Bearer {baseten_key}"},
            timeout=settings.listen_timeout_seconds,
        )
        return BackupListener(http, settings.baseten_model)
    if model_api is None:
        return None
    return BackupListener(model_api, settings.reasoning_model, reasoning_effort="low")


def _guest_space(settings: Settings, model: ReasoningModel, search: WebSearch | None) -> Space:
    """Sado for devices that did not sign in: same mind, a shared guest memory."""
    return _space_at(settings.guest_db_path, model, search)


_PERSON_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


def _personal_space(
    settings: Settings, person_id: str, model: ReasoningModel, search: WebSearch | None
) -> Space:
    """Sado for one signed-in person: their own memory, reminders and lists, no computer."""
    # Firebase ids are letters and digits; anything else must never become a file path.
    if not _PERSON_ID.match(person_id):
        raise InvalidIdentityError
    return _space_at(str(Path(settings.people_dir) / f"{person_id}.sqlite3"), model, search)


def _space_at(db_path: str, model: ReasoningModel, search: WebSearch | None) -> Space:
    memories = Memories(SqliteMemoryStore(db_path))
    reminders = Reminders(SqliteReminderStore(db_path))
    lists = Lists(SqliteListStore(db_path))
    return Space(Converse(model, memories, reminders, search, lists), memories, reminders, lists)


def _identity(settings: Settings) -> IdentityVerifier | None:
    if not settings.firebase_project_id.strip():
        return None
    return FirebaseIdentity(settings.firebase_project_id.strip())


def _web_search(settings: Settings, model_api: httpx.Client | None) -> WebSearch | None:
    if model_api is None:
        return None
    location = {
        "country": settings.search_country,
        "city": settings.search_city,
        "timezone": settings.search_timezone,
    }
    return MuseWebSearch(
        http=model_api,
        model=settings.reasoning_model,
        location={key: value for key, value in location.items() if value},
    )


def _default_reasoning_model(settings: Settings, model_api: httpx.Client | None) -> ReasoningModel:
    if model_api is not None:
        return MuseSparkReasoner(
            http=model_api,
            model=settings.reasoning_model,
            reasoning_effort=settings.reasoning_effort,
        )
    # Without a key, a developer may keep a private reasoner module outside version control.
    try:
        local = importlib.import_module("sado.infrastructure.reasoning.local_dev")
    except ModuleNotFoundError:
        return UnavailableReasoner()
    return cast(ReasoningModel, local.build_reasoner())


# One seam per layer keeps router tests hermetic without real models.
logger = logging.getLogger(__name__)

_WARM_UP_TEXT = {
    Language.UZBEK: "Salom.",
    Language.TAJIK: "Салом.",
    Language.RUSSIAN: "Привет.",
    Language.ENGLISH: "Hello.",
}


def _warm_up_voices(speak_text: SpeakText, languages: Sequence[Language]) -> None:
    # Voice models load on first use; without this the first spoken reply of a demo
    # waits for every model to load.
    for language in languages:
        try:
            speak_text.execute(_WARM_UP_TEXT[language], language)
        except SadoError:
            logger.warning("Could not warm up the %s voice", language)


def create_app(  # noqa: PLR0913
    *,
    language_packs: Mapping[Language, LanguagePack] | None = None,
    voice_catalog: VoiceCatalog | None = None,
    reasoning_model: ReasoningModel | None = None,
    document_explainer: DocumentExplainer | None = None,
    memory_store: MemoryStore | None = None,
    reminder_store: ReminderStore | None = None,
    web_search: WebSearch | None = None,
    list_store: ListStore | None = None,
    desktop: Desktop | None = None,
    desktop_token: str | None = None,
    identity: IdentityVerifier | None = None,
) -> FastAPI:
    settings = get_settings()
    catalog = voice_catalog or _voice_catalog(settings.default_voice)
    model_api = _model_api(settings)
    packs = language_packs or build_language_packs(
        _voice_config(settings), _backup_listener(settings, model_api)
    )
    speak_text = SpeakText(packs, catalog)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if settings.warm_up_voices:
            threading.Thread(
                target=_warm_up_voices, args=(speak_text, list(packs)), daemon=True
            ).start()
        yield

    app = FastAPI(title=settings.app_name, version=settings.version, lifespan=lifespan)
    app.state.voice_catalog = catalog
    app.state.speak_text = speak_text
    transcribe_speech = TranscribeSpeech(packs)
    app.state.transcribe_speech = transcribe_speech
    saved = Memories(memory_store or SqliteMemoryStore(settings.memory_db_path))
    alarms = Reminders(reminder_store or SqliteReminderStore(settings.memory_db_path))
    model = reasoning_model or _default_reasoning_model(settings, model_api)
    search = web_search or _web_search(settings, model_api)
    shopping = Lists(list_store or SqliteListStore(settings.memory_db_path))
    # Vision reuses the same thinker; a custom text-only reasoner keeps talking
    # while document explanations report the service as unavailable.
    if document_explainer is None:
        if isinstance(model, (MuseSparkReasoner, UnavailableReasoner)):
            document_explainer = model
        else:
            document_explainer = UnavailableReasoner()
    pending_actions = PendingActions()
    app.state.pending_actions = pending_actions
    computer = desktop or _desktop(settings)
    app.state.desktop_token = (desktop_token or _secret(settings.desktop_token)) if computer else ""
    hands = DesktopTools(computer, pending_actions, document_explainer) if computer else None
    owner = Space(Converse(model, saved, alarms, search, shopping, hands), saved, alarms, shopping)
    app.state.owner = owner
    app.state.identity = identity or _identity(settings)
    app.state.owner_emails = frozenset(
        email.strip().lower() for email in settings.owner_emails.split(",") if email.strip()
    )
    app.state.phone_inbox = PhoneInbox()
    # With nothing to tell people apart, one person uses Sado and it is the owner.
    strangers_possible = bool(app.state.desktop_token or app.state.identity)
    app.state.guest = _guest_space(settings, model, search) if strangers_possible else owner
    app.state.people = PersonalSpaces(
        lambda person_id: _personal_space(settings, person_id, model, search)
    )
    app.state.explain_document = ExplainDocument(
        document_explainer, CompositeDocumentReader(), transcribe_speech
    )

    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(speech.router)
    app.include_router(transcriptions.router)
    app.include_router(explanations.router)
    app.include_router(replies.router)
    app.include_router(voices.router)
    app.include_router(memories.router)
    app.include_router(reminders.router)
    app.include_router(lists.router)
    app.include_router(actions.router)
    app.include_router(phone.router)
    return app


app = create_app()
