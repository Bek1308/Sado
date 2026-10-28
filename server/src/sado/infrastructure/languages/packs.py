from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import httpx

from sado.domain.language import Language
from sado.domain.speech import LanguagePack, SpeechSynthesizer, TextNormalizer
from sado.infrastructure.asr.omnilingual import OmnilingualRecognizer
from sado.infrastructure.languages.english import build_english_normalizer
from sado.infrastructure.languages.russian import build_russian_normalizer
from sado.infrastructure.languages.tajik import build_tajik_normalizer
from sado.infrastructure.languages.uzbek import (
    build_uzbek_normalizer,
    transliterate_uzbek_to_cyrillic,
)
from sado.infrastructure.tts.decorators import (
    CueFreeSynthesizer,
    FallbackSynthesizer,
    TransliteratingSynthesizer,
)
from sado.infrastructure.tts.mms import MmsSpeechSynthesizer, VitsVoiceSettings
from sado.infrastructure.tts.mood_references import MoodReferenceLibrary
from sado.infrastructure.tts.omnivoice import CloneQuality, OmniVoiceEngine, OmniVoiceSynthesizer
from sado.infrastructure.tts.voice_presets import VoiceStyle

_NORMALIZERS: dict[Language, TextNormalizer] = {
    Language.TAJIK: build_tajik_normalizer(),
    Language.UZBEK: build_uzbek_normalizer(),
    Language.RUSSIAN: build_russian_normalizer(),
    Language.ENGLISH: build_english_normalizer(),
}

# Uzbek uses the "uzb" code: it reads numbers far better than "uzn" in our tests.
_OMNILINGUAL_CODES = {
    Language.TAJIK: "tgk_Cyrl",
    Language.UZBEK: "uzb_Latn",
    Language.RUSSIAN: "rus_Cyrl",
    Language.ENGLISH: "eng_Latn",
}

_MMS_MODEL_IDS = {
    Language.TAJIK: "facebook/mms-tts-tgk",
    Language.UZBEK: "facebook/mms-tts-uzb-script_cyrillic",
    Language.RUSSIAN: "facebook/mms-tts-rus",
    Language.ENGLISH: "facebook/mms-tts-eng",
}


@dataclass(frozen=True, slots=True)
class VoiceConfig:
    use_omnivoice: bool
    omnivoice_device: str
    omnivoice_uzbek_code: str
    voice_styles: Mapping[str, VoiceStyle]
    mood_reference_dir: Path
    clone_quality: CloneQuality
    mms_device: str
    mms_voice: VitsVoiceSettings
    asr_url: str
    asr_timeout_seconds: float


def build_language_packs(config: VoiceConfig) -> dict[Language, LanguagePack]:
    omnivoice = (
        OmniVoiceEngine(config.omnivoice_device, config.clone_quality)
        if config.use_omnivoice
        else None
    )
    asr_http = httpx.Client(base_url=config.asr_url, timeout=config.asr_timeout_seconds)
    return {
        language: LanguagePack(
            language=language,
            normalizer=_NORMALIZERS[language],
            synthesizer=_build_synthesizer(language, config, omnivoice),
            recognizer=OmnilingualRecognizer(asr_http, _OMNILINGUAL_CODES[language]),
        )
        for language in Language
    }


def _build_synthesizer(
    language: Language, config: VoiceConfig, omnivoice: OmniVoiceEngine | None
) -> SpeechSynthesizer:
    mms: SpeechSynthesizer = CueFreeSynthesizer(
        MmsSpeechSynthesizer(_MMS_MODEL_IDS[language], config.mms_voice, config.mms_device)
    )
    if language is Language.UZBEK:
        mms = TransliteratingSynthesizer(mms, transliterate_uzbek_to_cyrillic)
    if omnivoice is None:
        return mms

    code = config.omnivoice_uzbek_code if language is Language.UZBEK else language.value
    preferred = OmniVoiceSynthesizer(
        omnivoice, code, config.voice_styles, MoodReferenceLibrary(config.mood_reference_dir)
    )
    return FallbackSynthesizer(primary=preferred, fallback=mms)
