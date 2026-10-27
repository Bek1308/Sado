import pytest

from sado.infrastructure.languages.uzbek import (
    build_uzbek_normalizer,
    spell_uzbek_number,
    spell_uzbek_ordinal,
    transliterate_uzbek_to_cyrillic,
)


@pytest.mark.parametrize(
    ("number", "words"),
    [
        (0, "ноль"),
        (12, "ўн икки"),
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
def test_spells_cardinals(number: int, words: str) -> None:
    assert spell_uzbek_number(number) == words


@pytest.mark.parametrize(
    ("number", "words"),
    [
        (1, "биринчи"),
        (2, "иккинчи"),
        (5, "бешинчи"),
        (20, "йигирманчи"),
        (27, "йигирма еттинчи"),
        (2_026, "икки минг йигирма олтинчи"),
    ],
)
def test_spells_ordinals(number: int, words: str) -> None:
    assert spell_uzbek_ordinal(number) == words


@pytest.mark.parametrize(
    ("latin", "cyrillic"),
    [
        ("Salom, o'zbek do‘stlar!", "Салом, ўзбек дўстлар!"),
        ("Shahar", "Шаҳар"),
        ("ertaga", "эртага"),
        ("Yangi yil", "Янги йил"),
        ("ma'no", "маъно"),
        ("tog'", "тоғ"),
        ("Салом", "Салом"),
    ],
)
def test_transliterates_latin_to_cyrillic(latin: str, cyrillic: str) -> None:
    assert transliterate_uzbek_to_cyrillic(latin) == cyrillic


@pytest.mark.parametrize(
    ("text", "spoken"),
    [
        ("2026-yil", "икки минг йигирма олтинчи йил"),
        ("2026-yilda", "икки минг йигирма олтинчи йилда"),
        ("27-oktyabr", "йигирма еттинчи октябр"),
        ("27 oktyabr", "йигирма еттинчи октябр"),
        ("5ta olma", "бешта олма"),
        ("10dan ortiq", "ўндан ортиқ"),
        ("narxi 15 000 so'm", "нархи ўн беш минг сўм"),
        ("chegirma 20%", "чегирма йигирма фоиз"),
        ("Sado AI", "Садо эй ай"),
    ],
)
def test_normalizes_numbers_with_suffixes_and_names(text: str, spoken: str) -> None:
    assert build_uzbek_normalizer().normalize(text) == spoken
