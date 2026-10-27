import pytest

from sado.infrastructure.languages.english import build_english_normalizer


@pytest.mark.parametrize(
    ("text", "spoken"),
    [
        ("October 27, 2026", "October twenty-seventh, twenty twenty-six"),
        ("on May 3rd", "on May third"),
        ("the 21st floor", "the twenty-first floor"),
        ("born in 1999", "born in nineteen ninety-nine"),
        ("I have 3 cats", "I have three cats"),
        ("up 2.5%", "up two point five percent"),
        ("Sado uses AI", "Sado uses ay eye"),
    ],
)
def test_normalizes_english_text(text: str, spoken: str) -> None:
    assert build_english_normalizer().normalize(text) == spoken
