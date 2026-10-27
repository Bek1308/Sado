import re

from num2words import num2words

from sado.infrastructure.languages.pronunciation import (
    CYRILLIC_ACRONYMS,
    CYRILLIC_NAMES,
    FOREIGN_WORDS_TO_CYRILLIC,
    LATIN_ACRONYMS_IN_CYRILLIC,
    lexicon_rule,
)
from sado.infrastructure.languages.rules import (
    RulePipelineNormalizer,
    plain_number_rule,
    regex_rule,
)

_MONTHS_GENITIVE = (
    "января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря"
)
_LETTERS = r"[^\W\d_]+"

# Short endings written after a hyphen tell which case and gender the ordinal takes.
_ORDINAL_ENDINGS = {
    "й": ("nominative", "m"),
    "ый": ("nominative", "m"),
    "ий": ("nominative", "m"),
    "я": ("nominative", "f"),
    "е": ("nominative", "n"),
    "го": ("genitive", "m"),
    "му": ("dative", "m"),
    "м": ("prepositional", "m"),
    "ю": ("accusative", "f"),
}
_YEAR_CASES = {"год": "nominative", "года": "genitive", "году": "prepositional"}


def spell_russian_cardinal(number: int) -> str:
    return str(num2words(number, lang="ru"))


def spell_russian_ordinal(number: int, case: str, gender: str = "m") -> str:
    return str(num2words(number, lang="ru", to="ordinal", case=case, gender=gender))


def _spell_ordinal_ending(match: re.Match[str]) -> str:
    ending = match["ending"].lower()
    if ending not in _ORDINAL_ENDINGS:
        return spell_russian_cardinal(int(match["number"])) + match["ending"]
    case, gender = _ORDINAL_ENDINGS[ending]
    return spell_russian_ordinal(int(match["number"]), case, gender)


def build_russian_normalizer() -> RulePipelineNormalizer:
    return RulePipelineNormalizer(
        rules=(
            lexicon_rule(CYRILLIC_NAMES),
            LATIN_ACRONYMS_IN_CYRILLIC,
            CYRILLIC_ACRONYMS,
            FOREIGN_WORDS_TO_CYRILLIC,
            # "27 октября" -> "двадцать седьмого октября"
            regex_rule(
                rf"\b(?P<day>\d{{1,2}})\s+(?=(?:{_MONTHS_GENITIVE})\b)",
                lambda m: spell_russian_ordinal(int(m["day"]), "genitive", "n") + " ",
                re.IGNORECASE,
            ),
            # "2026 года" -> "две тысячи двадцать шестого года"
            regex_rule(
                r"\b(?P<year>\d+)\s+(?P<word>год[ау]?)\b",
                lambda m: (
                    f"{spell_russian_ordinal(int(m['year']), _YEAR_CASES[m['word'].lower()])} "
                    f"{m['word']}"
                ),
                re.IGNORECASE,
            ),
            # "5-й", "в 2026-м" -> ordinal in the case the ending shows.
            regex_rule(rf"(?P<number>\d+)-(?P<ending>{_LETTERS})", _spell_ordinal_ending),
            plain_number_rule(
                spell_russian_cardinal, decimal_word="целых", percent_word="процентов"
            ),
        )
    )
