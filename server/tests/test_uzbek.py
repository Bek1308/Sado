import pytest

from sado.infrastructure.languages.uzbek import (
    spell_uzbek_number,
    transliterate_uzbek_to_cyrillic,
)


@pytest.mark.parametrize(
    ("number", "words"),
    [
        (0, "ноль"),
        (7, "етти"),
        (12, "ўн икки"),
        (40, "қирқ"),
        (100, "юз"),
        (105, "юз беш"),
        (250, "икки юз эллик"),
        (1_000, "минг"),
        (1_999, "минг тўққиз юз тўқсон тўққиз"),
        (2_026, "икки минг йигирма олти"),
        (15_000, "ўн беш минг"),
        (1_000_000, "бир миллион"),
        (-3, "минус уч"),
    ],
)
def test_spells_numbers_in_cyrillic_uzbek(number: int, words: str) -> None:
    assert spell_uzbek_number(number) == words


@pytest.mark.parametrize(
    ("latin", "cyrillic"),
    [
        ("Salom, o'zbek do‘stlar!", "Салом, ўзбек дўстлар!"),
        ("Shahar", "Шаҳар"),
        ("ertaga", "эртага"),
        ("Yangi yil", "Янги йил"),
        ("ma'no", "маъно"),
        ("tog'", "тоғ"),
        ("choy", "чой"),
        ("Салом", "Салом"),
    ],
)
def test_transliterates_latin_uzbek_to_cyrillic(latin: str, cyrillic: str) -> None:
    assert transliterate_uzbek_to_cyrillic(latin) == cyrillic
