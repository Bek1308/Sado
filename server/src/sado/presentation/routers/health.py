from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from sado.infrastructure.settings import Settings, get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"]
    name: str
    version: str


@router.get("/health")
def read_health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    return HealthResponse(status="ok", name=settings.app_name, version=settings.version)
