"""Composition root: the only place where layers are wired together."""

from fastapi import FastAPI

from sado.infrastructure.settings import get_settings
from sado.presentation.routers import health


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.version)
    app.include_router(health.router)
    return app


app = create_app()
