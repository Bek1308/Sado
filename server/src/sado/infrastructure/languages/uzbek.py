"""Uzbek language pack.

Text is normalized to the official Latin alphabet, which speech models trained on modern
Uzbek read most naturally. Engines that need Cyrillic (MMS-TTS) convert at their own boundary.
"""

import re

from sado.infrastructure.languages.pronunciation import lexicon_rule
from sado.infrastructure.languages.rules import (
    RulePipelineNormalizer,
    plain_number_rule,
    regex_rule,
)

TURNED_COMMA = "ʻ"
"""The official letter mark in oʻ and gʻ."""
APOSTROPHE = "ʼ"
"""The official tutuq belgisi, as in maʼno."""

_UNITS = ("nol", "bir", "ikki", "uch", "toʻrt", "besh", "olti", "yetti", "sakkiz", "toʻqqiz")
_TENS = ("", "oʻn", "yigirma", "oʻttiz", "qirq", "ellik", "oltmish", "yetmish", "sakson", "toʻqson")
_HUNDRED = "yuz"
_THOUSAND = 1_000
_SCALES = ((1_000_000_000, "milliard"), (1_000_000, "million"), (_THOUSAND, "ming"))
_VOWELS = frozenset("aeiou")
_MONTHS = (
    "yanvar|fevral|mart|aprel|may|iyun|iyul|avgust|sentabr|sentyabr|oktabr|oktyabr|noyabr|dekabr"
)
_LETTERS = r"[^\W\d_]+"

_LATIN_NAMES = {
    "whatsapp": "vatsap",
    "youtube": "yutub",
    "google": "gugl",
    "facebook": "feysbuk",
    "iphone": "ayfon",
    "wi-fi": "vay-fay",
    "wifi": "vay-fay",
    "email": "imeyl",
    "muse": "myuz",
    "ok": "okey",
}
_LETTER_NAMES = {
    "a": "ey", "b": "bi", "c": "si", "d": "di", "e": "i", "f": "ef", "g": "ji", "h": "eych",
    "i": "ay", "j": "jey", "k": "key", "l": "el", "m": "em", "n": "en", "o": "ou", "p": "pi",
    "q": "kyu", "r": "ar", "s": "es", "t": "ti", "u": "yu", "v": "vi", "w": "dabl-yu",
    "x": "eks", "y": "uay", "z": "zed",
}  # fmt: skip


def spell_uzbek_number(number: int) -> str:
    if number < 0:
        return f"minus {spell_uzbek_number(-number)}"
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
    suffix = "nchi" if cardinal[-1] in _VOWELS else "inchi"
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


_CYRILLIC_TO_LATIN = {
    "а": "a", "б": "b", "в": "v", "г": "g", "ғ": "g" + TURNED_COMMA, "д": "d", "ё": "yo",
    "ж": "j", "з": "z", "и": "i", "й": "y", "к": "k", "қ": "q", "л": "l", "м": "m", "н": "n",
    "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ў": "o" + TURNED_COMMA,
    "ф": "f", "х": "x", "ҳ": "h", "ц": "ts", "ч": "ch", "ш": "sh", "ъ": APOSTROPHE, "ь": "",
    "э": "e", "ю": "yu", "я": "ya",
}  # fmt: skip
_CYRILLIC_VOWELS = frozenset("аеёиоуўэюя")


def transliterate_uzbek_to_latin(text: str) -> str:
    result: list[str] = []
    for index, char in enumerate(text):
        lower = char.lower()
        previous = text[index - 1].lower() if index else ""
        if lower == "е":
            # Cyrillic е is "ye" at the start of a word or after a vowel: ер -> yer, лекин -> lekin.
            starts_syllable = not previous.isalpha() or previous in _CYRILLIC_VOWELS
            converted = "ye" if starts_syllable else "e"
        else:
            converted = _CYRILLIC_TO_LATIN.get(lower, char)
        result.append(converted.capitalize() if char.isupper() else converted)
    return "".join(result)


_LETTER_MARK = re.compile(r"(?<=[OoGg])['\u2018\u2019\u02bc`]")
_TUTUQ = re.compile(r"(?<=[^\W\d_])['\u2018\u2019`](?=[^\W\d_])")


def unify_uzbek_apostrophes(text: str) -> str:
    """People type oʻ and gʻ with any of several quote marks; models learned the official ones."""
    return _TUTUQ.sub(APOSTROPHE, _LETTER_MARK.sub(TURNED_COMMA, text))


_LATIN_TO_CYRILLIC_DIGRAPHS = {
    "o" + TURNED_COMMA: "ў",
    "g" + TURNED_COMMA: "ғ",
    "sh": "ш",
    "ch": "ч",
    "yo": "ё",
    "yu": "ю",
    "ya": "я",
    "ye": "е",
}
_LATIN_TO_CYRILLIC = {
    "a": "а", "b": "б", "d": "д", "e": "е", "f": "ф", "g": "г", "h": "ҳ", "i": "и",
    "j": "ж", "k": "к", "l": "л", "m": "м", "n": "н", "o": "о", "p": "п", "q": "қ",
    "r": "р", "s": "с", "t": "т", "u": "у", "v": "в", "x": "х", "y": "й", "z": "з",
    "c": "ц", APOSTROPHE: "ъ",
}  # fmt: skip


def transliterate_uzbek_to_cyrillic(text: str) -> str:
    text = unify_uzbek_apostrophes(text)
    result: list[str] = []
    index = 0
    while index < len(text):
        char = text[index]
        pair = text[index : index + 2].lower()
        at_word_start = index == 0 or not text[index - 1].isalpha()
        if pair in _LATIN_TO_CYRILLIC_DIGRAPHS:
            converted, consumed = _LATIN_TO_CYRILLIC_DIGRAPHS[pair], 2
        elif char.lower() == "e" and at_word_start:
            converted, consumed = "э", 1
        else:
            converted, consumed = _LATIN_TO_CYRILLIC.get(char.lower(), char), 1
        result.append(converted.upper() if char.isupper() else converted)
        index += consumed
    return "".join(result)


def _spell_acronym(match: re.Match[str]) -> str:
    return " ".join(_LETTER_NAMES[letter.lower()] for letter in match[0])


def build_uzbek_normalizer() -> RulePipelineNormalizer:
    return RulePipelineNormalizer(
        rules=(
            transliterate_uzbek_to_latin,
            unify_uzbek_apostrophes,
            lexicon_rule(_LATIN_NAMES),
            regex_rule(r"\b[A-Z]{2,4}\b", _spell_acronym),
            # A hyphen marks an ordinal: "2026-yil" -> "ikki ming yigirma oltinchi yil".
            regex_rule(
                r"(?P<number>\d+)-(?=[^\W\d_])",
                lambda m: spell_uzbek_ordinal(int(m["number"])) + " ",
            ),
            # A day before a month is ordinal: "27 oktabr" -> "yigirma yettinchi oktabr".
            regex_rule(
                rf"\b(?P<day>\d{{1,2}})\s+(?=(?:{_MONTHS}))",
                lambda m: spell_uzbek_ordinal(int(m["day"])) + " ",
                re.IGNORECASE,
            ),
            # A suffix written right after the digits joins the number: "5ta" -> "beshta".
            regex_rule(
                rf"(?P<number>\d+)(?P<suffix>{_LETTERS})",
                lambda m: spell_uzbek_number(int(m["number"])) + m["suffix"],
            ),
            plain_number_rule(spell_uzbek_number, decimal_word="butun", percent_word="foiz"),
        )
    )
