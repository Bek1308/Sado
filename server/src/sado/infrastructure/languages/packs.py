from num2words import num2words

from sado.domain.language import Language
from sado.domain.speech import LanguagePack
from sado.infrastructure.languages.spoken_text_normalizer import (
    NumberSpeller,
    SpokenTextNormalizer,
)
from sado.infrastructure.languages.uzbek import (
    spell_uzbek_number,
    transliterate_uzbek_to_cyrillic,
)
from sado.infrastructure.tts.mms import MmsSpeechSynthesizer


def _num2words_speller(lang: str) -> NumberSpeller:
    def spell(number: int) -> str:
        return str(num2words(number, lang=lang))

    return spell


_NORMALIZERS = {
    Language.TAJIK: SpokenTextNormalizer(
        spell_number=_num2words_speller("tg"), decimal_word="бутун", percent_word="фоиз"
    ),
    Language.UZBEK: SpokenTextNormalizer(
        spell_number=spell_uzbek_number,
        decimal_word="бутун",
        percent_word="фоиз",
        transliterate=transliterate_uzbek_to_cyrillic,
    ),
    Language.RUSSIAN: SpokenTextNormalizer(
        spell_number=_num2words_speller("ru"), decimal_word="целых", percent_word="процентов"
    ),
    Language.ENGLISH: SpokenTextNormalizer(
        spell_number=_num2words_speller("en"), decimal_word="point", percent_word="percent"
    ),
}

_MMS_MODEL_IDS = {
    Language.TAJIK: "facebook/mms-tts-tgk",
    Language.UZBEK: "facebook/mms-tts-uzb-script_cyrillic",
    Language.RUSSIAN: "facebook/mms-tts-rus",
    Language.ENGLISH: "facebook/mms-tts-eng",
}


def build_language_packs(device: str) -> dict[Language, LanguagePack]:
    return {
        language: LanguagePack(
            language=language,
            normalizer=_NORMALIZERS[language],
            synthesizer=MmsSpeechSynthesizer(_MMS_MODEL_IDS[language], device=device),
        )
        for language in Language
    }
