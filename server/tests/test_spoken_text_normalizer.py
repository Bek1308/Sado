import pytest

from sado.infrastructure.languages.spoken_text_normalizer import SpokenTextNormalizer

_DIGIT_WORDS = {0: "zero", 1: "one", 2: "two", 5: "five", 15: "fifteen", 15_000: "fifteen-thousand"}


def _normalizer() -> SpokenTextNormalizer:
    return SpokenTextNormalizer(
        spell_number=_DIGIT_WORDS.__getitem__, decimal_word="point", percent_word="percent"
    )


@pytest.mark.parametrize(
    ("text", "spoken"),
    [
        ("I have 2 cats", "I have two cats"),
        ("Price: 15 000 somoni", "Price: fifteen-thousand somoni"),
        ("Rate 2.5", "Rate two point five"),
        ("Rate 2,05", "Rate two point zero five"),
        ("Growth 15%", "Growth fifteen percent"),
        ("No numbers here", "No numbers here"),
    ],
)
def test_turns_numbers_into_words(text: str, spoken: str) -> None:
    assert _normalizer().normalize(text) == spoken


def test_transliterates_before_spelling_numbers() -> None:
    normalizer = SpokenTextNormalizer(
        spell_number=_DIGIT_WORDS.__getitem__,
        decimal_word="point",
        percent_word="percent",
        transliterate=str.upper,
    )

    assert normalizer.normalize("buy 2 apples") == "BUY two APPLES"
