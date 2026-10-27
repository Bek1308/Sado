"""Building blocks for turning written text into text a speech model reads naturally."""

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass

type TextRule = Callable[[str], str]
type NumberSpeller = Callable[[int], str]
type MatchReplacer = Callable[[re.Match[str]], str]


@dataclass(frozen=True, slots=True)
class RulePipelineNormalizer:
    """Applies rules in order. Order matters: specific patterns must run before generic ones."""

    rules: Sequence[TextRule]

    def normalize(self, text: str) -> str:
        for rule in self.rules:
            text = rule(text)
        return text


def regex_rule(pattern: str, replace: MatchReplacer, flags: int = 0) -> TextRule:
    compiled = re.compile(pattern, flags)

    def apply(text: str) -> str:
        return compiled.sub(replace, text)

    return apply


_THOUSANDS_SEPARATOR = re.compile(r"(?<=\d)[^\S\r\n](?=\d{3}\b)")
_NUMBER = re.compile(r"(?P<integer>\d+)(?:[.,](?P<fraction>\d+))?(?P<percent>\s?%)?")


def plain_number_rule(spell: NumberSpeller, decimal_word: str, percent_word: str) -> TextRule:
    """Spells out whatever numbers the language-specific rules left untouched.

    Speech models read digits as noise, so this rule always runs last.
    """

    def spell_fraction(digits: str) -> str:
        significant = digits.lstrip("0")
        words = [spell(0)] * (len(digits) - len(significant))
        if significant:
            words.append(spell(int(significant)))
        return " ".join(words)

    def replace(match: re.Match[str]) -> str:
        words = [spell(int(match["integer"]))]
        if fraction := match["fraction"]:
            words += [decimal_word, spell_fraction(fraction)]
        if match["percent"]:
            words.append(percent_word)
        return " ".join(words)

    def apply(text: str) -> str:
        return _NUMBER.sub(replace, _THOUSANDS_SEPARATOR.sub("", text))

    return apply
