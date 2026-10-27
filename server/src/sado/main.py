"""Composition root: the only place where layers are wired together."""

from collections.abc import Mapping

from fastapi import FastAPI

from sado.application.speak_text import SpeakText
from sado.domain.language import Language
from sado.domain.speech import LanguagePack
from sado.infrastructure.languages.packs import VoiceConfig, build_language_packs
from sado.infrastructure.settings import Settings, get_settings
from sado.infrastructure.tts.mms import VitsVoiceSettings
from sado.presentation.error_handlers import register_error_handlers
from sado.presentation.routers import health, speech


def _voice_config(settings: Settings) -> VoiceConfig:
    return VoiceConfig(
        use_omnivoice=settings.use_omnivoice,
        omnivoice_device=settings.omnivoice_device,
        omnivoice_uzbek_code=settings.omnivoice_uzbek_code,
        voice_description=settings.voice_description,
        mms_device=settings.mms_device,
        mms_voice=VitsVoiceSettings(
            speaking_rate=settings.voice_speaking_rate,
            pitch_variation=settings.voice_pitch_variation,
            rhythm_variation=settings.voice_rhythm_variation,
        ),
    )


def create_app(language_packs: Mapping[Language, LanguagePack] | None = None) -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.version)

    packs = language_packs or build_language_packs(_voice_config(settings))
    app.state.speak_text = SpeakText(packs)

    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(speech.router)
    return app


app = create_app()
