import re
from collections.abc import Callable
from dataclasses import dataclass

type NumberSpeller = Callable[[int], str]
type Transliterator = Callable[[str], str]

# Speech models read digits as noise, so every number must reach them as words.
_THOUSANDS_SEPARATOR = re.compile(r"(?<=\d)[^\S\r\n](?=\d{3}\b)")
_NUMBER = re.compile(r"(?P<integer>\d+)(?:[.,](?P<fraction>\d+))?(?P<percent>\s?%)?")


@dataclass(frozen=True, slots=True)
class SpokenTextNormalizer:
    spell_number: NumberSpeller
    decimal_word: str
    percent_word: str
    transliterate: Transliterator | None = None

    def normalize(self, text: str) -> str:
        if self.transliterate is not None:
            text = self.transliterate(text)
        text = _THOUSANDS_SEPARATOR.sub("", text)
        return _NUMBER.sub(self._spell_match, text)

    def _spell_match(self, match: re.Match[str]) -> str:
        words = [self.spell_number(int(match["integer"]))]
        if fraction := match["fraction"]:
            words += [self.decimal_word, self._spell_fraction(fraction)]
        if match["percent"]:
            words.append(self.percent_word)
        return " ".join(words)

    def _spell_fraction(self, digits: str) -> str:
        leading_zeros = len(digits) - len(digits.lstrip("0"))
        zero_words = [self.spell_number(0)] * leading_zeros
        remainder = digits.lstrip("0")
        return " ".join(
            [*zero_words, self.spell_number(int(remainder))] if remainder else zero_words
        )
