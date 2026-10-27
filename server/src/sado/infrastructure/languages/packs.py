from sado.domain.language import Language
from sado.domain.speech import LanguagePack, TextNormalizer
from sado.infrastructure.languages.english import build_english_normalizer
from sado.infrastructure.languages.russian import build_russian_normalizer
from sado.infrastructure.languages.tajik import build_tajik_normalizer
from sado.infrastructure.languages.uzbek import build_uzbek_normalizer
from sado.infrastructure.tts.mms import MmsSpeechSynthesizer, VitsVoiceSettings

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


def build_language_packs(voice: VitsVoiceSettings, device: str) -> dict[Language, LanguagePack]:
    return {
        language: LanguagePack(
            language=language,
            normalizer=_NORMALIZERS[language],
            synthesizer=MmsSpeechSynthesizer(_MMS_MODEL_IDS[language], voice, device),
        )
        for language in Language
    }
