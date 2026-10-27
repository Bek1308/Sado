"""Pronunciation of words that do not belong to the language being spoken.

Names, brands and abbreviations sound the same in every language, so they get fixed
pronunciations instead of being guessed letter by letter by the speech model.
"""

import re
from collections.abc import Mapping

from sado.infrastructure.languages.rules import TextRule, regex_rule

CYRILLIC_NAMES = {
    "sado": "Садо",
    "meta": "Мета",
    "muse": "Мюз",
    "instagram": "Инстаграм",
    "telegram": "Телеграм",
    "whatsapp": "Ватсап",
    "youtube": "Ютуб",
    "google": "Гугл",
    "facebook": "Фейсбук",
    "iphone": "айфон",
    "android": "андроид",
    "wi-fi": "вай-фай",
    "wifi": "вай-фай",
    "email": "имейл",
    "ok": "окей",
}

LATIN_LETTERS_IN_CYRILLIC = {
    "a": "эй", "b": "би", "c": "си", "d": "ди", "e": "и", "f": "эф", "g": "джи",
    "h": "эйч", "i": "ай", "j": "джей", "k": "кей", "l": "эл", "m": "эм", "n": "эн",
    "o": "оу", "p": "пи", "q": "кью", "r": "ар", "s": "эс", "t": "ти", "u": "ю",
    "v": "ви", "w": "дабл-ю", "x": "экс", "y": "уай", "z": "зед",
}  # fmt: skip

CYRILLIC_LETTER_NAMES = {
    "а": "а", "б": "бэ", "в": "вэ", "г": "гэ", "ғ": "ғе", "д": "дэ", "е": "е", "ж": "жэ",
    "з": "зэ", "и": "и", "к": "ка", "қ": "қе", "л": "эл", "м": "эм", "н": "эн", "о": "о",
    "п": "пэ", "р": "эр", "с": "эс", "т": "тэ", "у": "у", "ф": "эф", "х": "ха", "ҳ": "ҳе",
    "ц": "цэ", "ч": "че", "ҷ": "ҷе", "ш": "ша", "э": "э", "ю": "ю", "я": "я",
}  # fmt: skip

ENGLISH_LETTER_NAMES = {
    "a": "ay", "b": "bee", "c": "see", "d": "dee", "e": "ee", "f": "eff", "g": "jee",
    "h": "aitch", "i": "eye", "j": "jay", "k": "kay", "l": "ell", "m": "em", "n": "en",
    "o": "oh", "p": "pee", "q": "cue", "r": "ar", "s": "ess", "t": "tee", "u": "you",
    "v": "vee", "w": "double you", "x": "ex", "y": "why", "z": "zee",
}  # fmt: skip

_ACRONYM_LENGTH = "{2,4}"


def lexicon_rule(pronunciations: Mapping[str, str]) -> TextRule:
    """Replaces whole words, ignoring case, with their fixed pronunciation."""
    lookup = {word.lower(): spoken for word, spoken in pronunciations.items()}
    alternatives = "|".join(re.escape(word) for word in sorted(lookup, key=len, reverse=True))
    return regex_rule(
        rf"(?<![\w-])(?:{alternatives})(?![\w-])",
        lambda match: lookup[match[0].lower()],
        re.IGNORECASE,
    )


def acronym_rule(letter_names: Mapping[str, str], uppercase_letters: str) -> TextRule:
    """Spells short all-caps words letter by letter: "AI" becomes "эй ай"."""
    return regex_rule(
        rf"\b[{uppercase_letters}]{_ACRONYM_LENGTH}\b",
        lambda match: " ".join(letter_names[letter.lower()] for letter in match[0]),
    )


LATIN_ACRONYMS_IN_CYRILLIC = acronym_rule(LATIN_LETTERS_IN_CYRILLIC, "A-Z")
CYRILLIC_ACRONYMS = acronym_rule(CYRILLIC_LETTER_NAMES, "АБВГҒДЕЖЗИКҚЛМНОПРСТУФХҲЦЧҶШЭЮЯ")
ENGLISH_ACRONYMS = acronym_rule(ENGLISH_LETTER_NAMES, "A-Z")

_FOREIGN_DIGRAPHS = {
    "sh": "ш", "ch": "ч", "zh": "ж", "kh": "х", "ts": "ц", "th": "т", "ph": "ф",
    "oo": "у", "ee": "и", "ya": "я", "yu": "ю", "yo": "ё",
}  # fmt: skip
_FOREIGN_LETTERS = {
    "a": "а", "b": "б", "c": "к", "d": "д", "e": "е", "f": "ф", "g": "г", "h": "х",
    "i": "и", "j": "дж", "k": "к", "l": "л", "m": "м", "n": "н", "o": "о", "p": "п",
    "q": "к", "r": "р", "s": "с", "t": "т", "u": "у", "v": "в", "w": "в", "x": "кс",
    "y": "й", "z": "з",
}  # fmt: skip


def _transliterate_foreign_word(match: re.Match[str]) -> str:
    word = match[0]
    result: list[str] = []
    index = 0
    while index < len(word):
        pair = word[index : index + 2].lower()
        if pair in _FOREIGN_DIGRAPHS:
            converted, index = _FOREIGN_DIGRAPHS[pair], index + 2
        else:
            converted, index = _FOREIGN_LETTERS.get(word[index].lower(), word[index]), index + 1
        result.append(converted)
    spoken = "".join(result)
    return spoken.capitalize() if word[0].isupper() else spoken


FOREIGN_WORDS_TO_CYRILLIC = regex_rule(r"[A-Za-z]+", _transliterate_foreign_word)
"""Lets Cyrillic speech models pronounce leftover Latin-script words instead of skipping them."""
