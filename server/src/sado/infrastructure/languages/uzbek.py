"""Uzbek language pack. MMS-TTS reads Uzbek from Cyrillic, so all output is Cyrillic."""

import re

from sado.infrastructure.languages.pronunciation import (
    CYRILLIC_NAMES,
    LATIN_ACRONYMS_IN_CYRILLIC,
    lexicon_rule,
)
from sado.infrastructure.languages.rules import (
    RulePipelineNormalizer,
    plain_number_rule,
    regex_rule,
)

_UNITS = ("ноль", "бир", "икки", "уч", "тўрт", "беш", "олти", "етти", "саккиз", "тўққиз")
_TENS = ("", "ўн", "йигирма", "ўттиз", "қирқ", "эллик", "олтмиш", "етмиш", "саксон", "тўқсон")
_HUNDRED = "юз"
_THOUSAND = 1_000
_SCALES = ((1_000_000_000, "миллиард"), (1_000_000, "миллион"), (_THOUSAND, "минг"))
_VOWELS = frozenset("аеёиоуўэюя")
_MONTHS = "январ|феврал|март|апрел|май|июн|июл|август|сентябр|октябр|ноябр|декабр"
_LETTERS = r"[^\W\d_]+"


def spell_uzbek_number(number: int) -> str:
    if number < 0:
        return f"минус {spell_uzbek_number(-number)}"
    if number == 0:
        return _UNITS[0]

    words: list[str] = []
    for scale, scale_word in _SCALES:
        count, number = divmod(number, scale)
        if count == 1 and scale == _THOUSAND:
            words.append(scale_word)
        elif count:
            words += [*_spell_below_thousand(count), scale_word]
    words += _spell_below_thousand(number)
    return " ".join(words)


def spell_uzbek_ordinal(number: int) -> str:
    cardinal = spell_uzbek_number(number)
    suffix = "нчи" if cardinal[-1] in _VOWELS else "инчи"
    return cardinal + suffix


def _spell_below_thousand(number: int) -> list[str]:
    hundreds, remainder = divmod(number, 100)
    tens, units = divmod(remainder, 10)

    words: list[str] = []
    if hundreds:
        words += [_UNITS[hundreds], _HUNDRED] if hundreds > 1 else [_HUNDRED]
    if tens:
        words.append(_TENS[tens])
    if units:
        words.append(_UNITS[units])
    return words


_APOSTROPHES = frozenset("'‘’ʻʼ`")
_DIGRAPHS = {
    "sh": "ш",
    "ch": "ч",
    "yo": "ё",
    "yu": "ю",
    "ya": "я",
    "ye": "е",
}
_LETTER_MAP = {
    "a": "а", "b": "б", "d": "д", "e": "е", "f": "ф", "g": "г", "h": "ҳ", "i": "и",
    "j": "ж", "k": "к", "l": "л", "m": "м", "n": "н", "o": "о", "p": "п", "q": "қ",
    "r": "р", "s": "с", "t": "т", "u": "у", "v": "в", "x": "х", "y": "й", "z": "з",
    "c": "ц",
}  # fmt: skip
_MODIFIED_LETTERS = {"o": "ў", "g": "ғ"}
_HARD_SIGN = "ъ"
_WORD_INITIAL_E = "э"


def transliterate_uzbek_to_cyrillic(text: str) -> str:
    result: list[str] = []
    index = 0
    while index < len(text):
        char = text[index]
        lower = char.lower()
        following = text[index + 1] if index + 1 < len(text) else ""
        at_word_start = index == 0 or not text[index - 1].isalpha()

        if lower in _MODIFIED_LETTERS and following in _APOSTROPHES:
            converted, consumed = _MODIFIED_LETTERS[lower], 2
        elif (lower + following.lower()) in _DIGRAPHS:
            converted, consumed = _DIGRAPHS[lower + following.lower()], 2
        elif lower == "e" and at_word_start:
            converted, consumed = _WORD_INITIAL_E, 1
        elif lower in _LETTER_MAP:
            converted, consumed = _LETTER_MAP[lower], 1
        elif char in _APOSTROPHES and index > 0 and text[index - 1].isalpha():
            converted, consumed = _HARD_SIGN, 1
        else:
            converted, consumed = char, 1

        result.append(converted.upper() if char.isupper() else converted)
        index += consumed
    return "".join(result)


def build_uzbek_normalizer() -> RulePipelineNormalizer:
    return RulePipelineNormalizer(
        rules=(
            lexicon_rule(CYRILLIC_NAMES),
            LATIN_ACRONYMS_IN_CYRILLIC,
            transliterate_uzbek_to_cyrillic,
            # A hyphen marks an ordinal: "2026-йил", "5-синф" -> "...олтинчи йил", "бешинчи синф".
            regex_rule(
                r"(?P<number>\d+)-(?=[^\W\d_])",
                lambda m: spell_uzbek_ordinal(int(m["number"])) + " ",
            ),
            # A day before a month is ordinal: "27 октябр" -> "йигирма еттинчи октябр".
            regex_rule(
                rf"\b(?P<day>\d{{1,2}})\s+(?=(?:{_MONTHS}))",
                lambda m: spell_uzbek_ordinal(int(m["day"])) + " ",
                re.IGNORECASE,
            ),
            # A suffix written right after the digits joins the number: "5та" -> "бешта".
            regex_rule(
                rf"(?P<number>\d+)(?P<suffix>{_LETTERS})",
                lambda m: spell_uzbek_number(int(m["number"])) + m["suffix"],
            ),
            plain_number_rule(spell_uzbek_number, decimal_word="бутун", percent_word="фоиз"),
        )
    )
