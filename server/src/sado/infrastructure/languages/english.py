import re

from num2words import num2words

from sado.infrastructure.languages.pronunciation import ENGLISH_ACRONYMS
from sado.infrastructure.languages.rules import (
    RulePipelineNormalizer,
    plain_number_rule,
    regex_rule,
)

_MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
_EARLIEST_YEAR = 1100
_LATEST_YEAR = 2099


def spell_english_cardinal(number: int) -> str:
    return str(num2words(number, lang="en"))


def spell_english_ordinal(number: int) -> str:
    return str(num2words(number, lang="en", to="ordinal"))


def spell_english_year(year: int) -> str:
    if _EARLIEST_YEAR <= year <= _LATEST_YEAR:
        return str(num2words(year, lang="en", to="year"))
    return spell_english_cardinal(year)


def _spell_date(match: re.Match[str]) -> str:
    spoken = f"{match['month']} {spell_english_ordinal(int(match['day']))}"
    if year := match["year"]:
        spoken += f", {spell_english_year(int(year))}"
    return spoken


def build_english_normalizer() -> RulePipelineNormalizer:
    return RulePipelineNormalizer(
        rules=(
            ENGLISH_ACRONYMS,
            # "October 27, 2026" -> "October twenty-seventh, twenty twenty-six"
            regex_rule(
                rf"\b(?P<month>{_MONTHS})\s+(?P<day>\d{{1,2}})(?:st|nd|rd|th)?"
                r"(?:,\s*(?P<year>\d{4}))?\b",
                _spell_date,
            ),
            # "27th" -> "twenty-seventh"
            regex_rule(
                r"\b(?P<number>\d+)(?:st|nd|rd|th)\b",
                lambda m: spell_english_ordinal(int(m["number"])),
                re.IGNORECASE,
            ),
            # "in 2026" -> "in twenty twenty-six"
            regex_rule(
                r"\b(?P<preposition>in|since|by|until|of)\s+(?P<year>\d{4})\b",
                lambda m: f"{m['preposition']} {spell_english_year(int(m['year']))}",
                re.IGNORECASE,
            ),
            plain_number_rule(spell_english_cardinal, decimal_word="point", percent_word="percent"),
        )
    )
