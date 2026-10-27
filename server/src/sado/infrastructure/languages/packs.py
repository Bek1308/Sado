from dataclasses import dataclass

from sado.domain.language import Language
from sado.domain.speech import LanguagePack, SpeechSynthesizer, TextNormalizer
from sado.infrastructure.languages.english import build_english_normalizer
from sado.infrastructure.languages.russian import build_russian_normalizer
from sado.infrastructure.languages.tajik import build_tajik_normalizer
from sado.infrastructure.languages.uzbek import (
    build_uzbek_normalizer,
    transliterate_uzbek_to_cyrillic,
)
from sado.infrastructure.tts.decorators import FallbackSynthesizer, TransliteratingSynthesizer
from sado.infrastructure.tts.mms import MmsSpeechSynthesizer, VitsVoiceSettings
from sado.infrastructure.tts.omnivoice import OmniVoiceEngine, OmniVoiceSynthesizer

_NORMALIZERS: dict[Language, TextNormalizer] = {
    Language.TAJIK: build_tajik_normalizer(),
    Language.UZBEK: build_uzbek_normalizer(),
    Language.RUSSIAN: build_russian_normalizer(),
    Language.ENGLISH: build_english_normalizer(),
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
    voice_description: str
    mms_device: str
    mms_voice: VitsVoiceSettings


def build_language_packs(config: VoiceConfig) -> dict[Language, LanguagePack]:
    omnivoice = OmniVoiceEngine(config.omnivoice_device) if config.use_omnivoice else None
    return {
        language: LanguagePack(
            language=language,
            normalizer=_NORMALIZERS[language],
            synthesizer=_build_synthesizer(language, config, omnivoice),
        )
        for language in Language
    }


def _build_synthesizer(
    language: Language, config: VoiceConfig, omnivoice: OmniVoiceEngine | None
) -> SpeechSynthesizer:
    mms: SpeechSynthesizer = MmsSpeechSynthesizer(
        _MMS_MODEL_IDS[language], config.mms_voice, config.mms_device
    )
    if language is Language.UZBEK:
        mms = TransliteratingSynthesizer(mms, transliterate_uzbek_to_cyrillic)
    if omnivoice is None:
        return mms

    code = config.omnivoice_uzbek_code if language is Language.UZBEK else language.value
    preferred = OmniVoiceSynthesizer(omnivoice, code, config.voice_description)
    return FallbackSynthesizer(primary=preferred, fallback=mms)
