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
    warm_up_voices: bool = True
    mood_reference_dir: str = "data/voices"
    clone_num_steps: int = 64
    clone_guidance_scale: float = 3.0

    memory_db_path: str = "data/memory.sqlite3"

    meta_api_key: SecretStr | None = None
    meta_api_url: str = "https://api.meta.ai/v1"
    reasoning_model: str = "muse-spark-1.3"
    reasoning_effort: str = "low"
    # Up to four model calls per reply must fit inside the app's 120-second wait.
    reasoning_timeout_seconds: float = 25.0
    # Approximate place for web searches, so "weather" means the user's weather.
    search_country: str = "TJ"
    search_city: str = "Dushanbe"
    search_timezone: str = "Asia/Dushanbe"

    asr_url: str = "http://localhost:8011"
    # Language detection may transcribe the same clip up to four times.
    asr_timeout_seconds: float = 20.0

    mms_device: str = "cpu"
    voice_speaking_rate: float = 1.0
    voice_pitch_variation: float = 0.5
    voice_rhythm_variation: float = 0.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
