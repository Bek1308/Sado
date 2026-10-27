"""Composition root: the only place where layers are wired together."""

from collections.abc import Mapping

from fastapi import FastAPI

from sado.application.speak_text import SpeakText
from sado.domain.language import Language
from sado.domain.speech import LanguagePack
from sado.infrastructure.languages.packs import build_language_packs
from sado.infrastructure.settings import get_settings
from sado.presentation.error_handlers import register_error_handlers
from sado.presentation.routers import health, speech


def create_app(language_packs: Mapping[Language, LanguagePack] | None = None) -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.version)

    packs = language_packs or build_language_packs(device=settings.speech_device)
    app.state.speak_text = SpeakText(packs)

    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(speech.router)
    return app


app = create_app()
