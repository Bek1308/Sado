from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SADO_", env_file=".env", extra="ignore")

    app_name: str = "Sado"
    version: str = "0.1.0"
    environment: str = "development"

    use_omnivoice: bool = True
    omnivoice_device: str = "cuda"
    omnivoice_uzbek_code: str = "uz"
    default_voice: str = "sado"

    mms_device: str = "cpu"
    voice_speaking_rate: float = 1.0
    voice_pitch_variation: float = 0.5
    voice_rhythm_variation: float = 0.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
