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

_MONTHS = "январ|феврал|март|апрел|май|июн|июл|август|сентябр|октябр|ноябр|декабр"
_LETTERS = r"[^\W\d_]+"


def spell_tajik_cardinal(number: int) -> str:
    return str(num2words(number, lang="tg"))


def spell_tajik_ordinal(number: int) -> str:
    return str(num2words(number, lang="tg", to="ordinal"))


def build_tajik_normalizer() -> RulePipelineNormalizer:
    return RulePipelineNormalizer(
        rules=(
            lexicon_rule(CYRILLIC_NAMES),
            LATIN_ACRONYMS_IN_CYRILLIC,
            CYRILLIC_ACRONYMS,
            FOREIGN_WORDS_TO_CYRILLIC,
            # "27-уми" -> "бисту ҳафтуми"
            regex_rule(
                r"(?P<number>\d+)-(?:ум|юм|ӯм)(?P<izofat>и?)\b",
                lambda m: spell_tajik_ordinal(int(m["number"])) + m["izofat"],
            ),
            # A day before a month is ordinal: "27 октябри" -> "бисту ҳафтуми октябри".
            regex_rule(
                rf"\b(?P<day>\d{{1,2}})\s+(?=(?:{_MONTHS}))",
                lambda m: f"{spell_tajik_ordinal(int(m['day']))}и ",
                re.IGNORECASE,
            ),
            # Any other suffix joins the last spoken word: "2026-ро", "5то" -> "...шашро", "панҷто".
            regex_rule(
                rf"(?P<number>\d+)-?(?P<suffix>{_LETTERS})",
                lambda m: spell_tajik_cardinal(int(m["number"])) + m["suffix"],
            ),
            plain_number_rule(spell_tajik_cardinal, decimal_word="бутун", percent_word="фоиз"),
        )
    )
