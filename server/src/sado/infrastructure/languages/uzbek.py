"""Uzbek helpers. MMS-TTS speaks Uzbek from Cyrillic text, so everything is produced in Cyrillic."""

_UNITS = ("ноль", "бир", "икки", "уч", "тўрт", "беш", "олти", "етти", "саккиз", "тўққиз")
_TENS = ("", "ўн", "йигирма", "ўттиз", "қирқ", "эллик", "олтмиш", "етмиш", "саксон", "тўқсон")
_HUNDRED = "юз"
_THOUSAND = 1_000
_SCALES = ((1_000_000_000, "миллиард"), (1_000_000, "миллион"), (_THOUSAND, "минг"))


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


_APOSTROPHES = frozenset("'\u2018\u2019\u02bb\u02bc`")
_DIGRAPHS = {
    "sh": "ш",
    "ch": "ч",
    "yo": "ё",
    "yu": "ю",
    "ya": "я",
    "ye": "е",
}
_LETTERS = {
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
        elif lower in _LETTERS:
            converted, consumed = _LETTERS[lower], 1
        elif char in _APOSTROPHES and index > 0 and text[index - 1].isalpha():
            converted, consumed = _HARD_SIGN, 1
        else:
            converted, consumed = char, 1

        result.append(converted.upper() if char.isupper() else converted)
        index += consumed
    return "".join(result)
