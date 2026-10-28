from functools import lru_cache

from pydantic import SecretStr
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
    mood_reference_dir: str = "data/voices"
    clone_num_steps: int = 64
    clone_guidance_scale: float = 3.0

    memory_db_path: str = "data/memory.sqlite3"

    meta_api_key: SecretStr | None = None
    meta_api_url: str = "https://api.meta.ai/v1"
    reasoning_model: str = "muse-spark-1.3"
    reasoning_effort: str = "low"
    reasoning_timeout_seconds: float = 60.0

    asr_url: str = "http://localhost:8011"
    asr_timeout_seconds: float = 60.0

    mms_device: str = "cpu"
    voice_speaking_rate: float = 1.0
    voice_pitch_variation: float = 0.5
    voice_rhythm_variation: float = 0.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
