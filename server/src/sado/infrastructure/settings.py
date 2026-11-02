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
    # Off unless the owner turns it on: Sado may then read and drive this computer's
    # windows, always asking before it types, closes or runs anything.
    desktop_control: bool = False
    # Only requests carrying this token may use the computer, so a tunnel that exposes
    # the server to a phone never exposes the computer with it.
    desktop_token: SecretStr | None = None
    # Listen on the computer's microphone for "Sado", which opens the voice bar. The small
    # Vosk model runs on the computer; nothing it hears leaves it.
    wake_word: bool = False
    wake_model_dir: str = "data/wake/vosk-model-small-ru-0.22"
    mood_reference_dir: str = "data/voices"
    clone_num_steps: int = 64
    clone_guidance_scale: float = 3.0

    memory_db_path: str = "data/memory.sqlite3"
    # Once desktop control is on, devices without its token are guests, e.g. judges
    # trying Sado through a tunnel: they get their own memories, reminders and lists here.
    guest_db_path: str = "data/guests.sqlite3"
    # Sign-in with Google through Firebase: everyone who signs in gets their own memory
    # under people_dir, and a phone signed in with one of the owner's addresses
    # (comma-separated) is the owner's and may drive the computer.
    firebase_project_id: str = ""
    owner_emails: str = ""
    people_dir: str = "data/people"

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

    # Muse Spark Open on Baseten hears speech when the Omnilingual worker is away, e.g.
    # on a host without a GPU. Without a key, Muse on the Model API listens instead.
    baseten_api_key: SecretStr | None = None
    baseten_url: str = "https://inference.baseten.co/v1"
    baseten_model: str = "meta-models/muse-spark-open-1026"
    listen_timeout_seconds: float = 30.0

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
